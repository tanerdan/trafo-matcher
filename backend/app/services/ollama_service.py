import httpx
import json
import re
from typing import Dict, List, Optional, Any


class OllamaService:
    """Ollama ile iletişim kuran servis - Doğal dil sorgularını parse eder"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model

    async def check_connection(self) -> bool:
        """Ollama bağlantısını kontrol et"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False

    async def get_available_models(self) -> List[str]:
        """Mevcut modelleri listele"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def _build_extraction_prompt(self, user_query: str) -> str:
        """Parametre çıkarma için prompt oluştur"""
        return f"""Sen bir trafo (transformatör) spesifikasyon uzmanısın.
Kullanıcının doğal dilde yazdığı trafo talebinden SADECE açıkça belirtilen teknik parametreleri çıkar.

ÖNEMLİ KURALLAR:
1. SADECE kullanıcının açıkça yazdığı değerleri çıkar
2. Tahmin yapma, varsayılan değer ekleme
3. Belirtilmeyen parametreleri JSON'a DAHİL ETME
4. Emin olmadığın parametreleri ekleme

Çıkarılabilecek parametreler:
- rating_kva: Güç (kVA) - örn: "100 kVA", "250kVA"
- high_voltage_v: Yüksek gerilim (V) - örn: "11000V", "33kV", "11000/415"
- low_voltage_v: Alçak gerilim (V) - örn: "415V", "400V"
- frequency_hz: Frekans (Hz) - örn: "50Hz", "60Hz"
- vector_group: Bağlantı grubu - örn: "Dyn11", "Yyn0", "Dd0"
- no_load_loss_w: Boşta kayıp (W) - örn: "P0=130W", "boşta kayıp 150W"
- load_loss_w: Yük kaybı (W) - örn: "Pk=1250W", "yük kaybı 1500W"
- impedance_percent: Empedans (%) - örn: "Ucc=4.75%", "empedans %4"
- cooling_type: Soğutma tipi - örn: "ONAN", "ONAF"
- lv_material: AG sargı malzemesi - örn: "bakır", "alüminyum", "cu", "al"
- hv_material: YG sargı malzemesi - örn: "bakır", "alüminyum", "cu", "al"

Kullanıcı sorgusu: "{user_query}"

SADECE metinde açıkça geçen parametreleri içeren JSON döndür. Boş obje {{}} döndürmek de geçerlidir.

JSON:"""

    def _build_explanation_prompt(
        self,
        user_query: str,
        extracted_params: Dict,
        matches: List[Dict]
    ) -> str:
        """Sonuçları açıklama için prompt oluştur"""
        matches_text = "\n".join([
            f"- {m['design_number']}: {m['similarity_score']*100:.1f}% benzerlik, "
            f"{m['specs'].get('rating_kva', 'N/A')} kVA, "
            f"{m['specs'].get('high_voltage_v', 'N/A')}/{m['specs'].get('low_voltage_v', 'N/A')} V"
            for m in matches[:3]
        ])

        return f"""Sen bir trafo uzmanısın. Kullanıcının trafo arama sonuçlarını Türkçe olarak kısaca açıkla.

Kullanıcı talebi: "{user_query}"

Çıkarılan parametreler: {json.dumps(extracted_params, ensure_ascii=False)}

Bulunan en yakın dizaynlar:
{matches_text}

Kısa ve öz bir açıklama yaz (2-3 cümle). Hangi parametrelerin eşleştiğini ve farklılıkları belirt."""

    async def extract_parameters(self, user_query: str) -> Dict[str, Any]:
        """Doğal dil sorgusundan trafo parametrelerini çıkar"""
        # Önce basit regex ile dene (LLM yoksa veya hata olursa)
        params = self._extract_with_regex(user_query)

        # Ollama ile daha akıllı çıkarım dene
        try:
            async with httpx.AsyncClient() as client:
                prompt = self._build_extraction_prompt(user_query)

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 500
                        }
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("response", "")

                    # JSON'u parse et
                    llm_params = self._parse_json_response(llm_response)
                    if llm_params:
                        # LLM sonuçlarını regex sonuçlarına EKLE (üzerine yazma)
                        # Sadece regex'te olmayan parametreleri ekle
                        for key, value in llm_params.items():
                            if key not in params and value is not None:
                                params[key] = value

        except Exception as e:
            print(f"Ollama error: {e}")

        return params

    def _extract_with_regex(self, query: str) -> Dict[str, Any]:
        """Basit regex ile parametre çıkar (fallback)"""
        params = {}
        query_lower = query.lower()

        # Güç (kVA)
        kva_match = re.search(r"(\d+)\s*kva", query_lower)
        if kva_match:
            params["rating_kva"] = float(kva_match.group(1))

        # Yüksek gerilim
        # 11000V, 33kV, 11000/415V gibi formatları yakala
        # NOT: kVA ile karışmaması için kV'den önce boşluk veya başlangıç olmalı
        hv_match = re.search(r"(\d{4,5})\s*v(?!a)", query_lower)  # 11000V (kVA değil)
        if hv_match:
            params["high_voltage_v"] = float(hv_match.group(1))
        else:
            # kV araması - kVA ile karışmaması için sadece kv olmalı
            hv_match = re.search(r"(?<!\d)(\d{1,3})\s*kv(?!a)", query_lower)  # 33kV (kVA değil)
            if hv_match:
                params["high_voltage_v"] = float(hv_match.group(1)) * 1000

        # Alçak gerilim
        lv_patterns = [
            r"(\d+)\s*v?\s*(ag|alçak|lv|low)",
            r"(ag|alçak|lv|low)\s*(\d+)\s*v",
            r"\d+\s*/\s*(\d{3,4})\s*v",  # 11000/415 V formatı
        ]
        for pattern in lv_patterns:
            match = re.search(pattern, query_lower)
            if match:
                for g in match.groups():
                    if g and g.isdigit():
                        params["low_voltage_v"] = float(g)
                        break
                break

        # Vektör grubu
        vg_match = re.search(r"(dyn?\d+|yyn?\d+|dd\d+|yy\d+)", query_lower)
        if vg_match:
            params["vector_group"] = vg_match.group(1).upper()

        # Frekans
        freq_match = re.search(r"(\d+)\s*hz", query_lower)
        if freq_match:
            params["frequency_hz"] = float(freq_match.group(1))

        # Soğutma tipi
        cooling_match = re.search(r"(onan|onaf|ofaf|ofwf)", query_lower)
        if cooling_match:
            params["cooling_type"] = cooling_match.group(1).upper()

        # Kayıplar
        nll_match = re.search(r"boşta\s*kayıp\s*(\d+)\s*w?|p0\s*[:=]?\s*(\d+)", query_lower)
        if nll_match:
            value = nll_match.group(1) or nll_match.group(2)
            params["no_load_loss_w"] = float(value)

        ll_match = re.search(r"yük\s*kayb\s*(\d+)\s*w?|pk\s*[:=]?\s*(\d+)", query_lower)
        if ll_match:
            value = ll_match.group(1) or ll_match.group(2)
            params["load_loss_w"] = float(value)

        # Empedans
        imp_match = re.search(r"empedans\s*(\d+\.?\d*)\s*%?|ucc?\s*[:=]?\s*(\d+\.?\d*)", query_lower)
        if imp_match:
            value = imp_match.group(1) or imp_match.group(2)
            params["impedance_percent"] = float(value)

        # Malzeme
        if "bakır" in query_lower or "bakir" in query_lower or " cu " in query_lower or query_lower.endswith(" cu"):
            params["lv_material"] = "cu"
            params["hv_material"] = "cu"
        elif "alüminyum" in query_lower or "aluminyum" in query_lower or " al " in query_lower:
            params["lv_material"] = "al"
            params["hv_material"] = "al"

        return params

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """LLM yanıtından JSON'u parse et - null ve None değerleri filtrele"""
        parsed = None

        try:
            # Direkt JSON dene
            parsed = json.loads(response)
        except json.JSONDecodeError:
            pass

        if not parsed:
            # JSON bloğunu bul
            json_match = re.search(r"\{[^{}]*\}", response)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

        if parsed:
            # null, None ve boş değerleri filtrele
            filtered = {
                k: v for k, v in parsed.items()
                if v is not None and v != "" and v != "null" and v != "None"
            }
            return filtered if filtered else None

        return None

    async def generate_explanation(
        self,
        user_query: str,
        extracted_params: Dict,
        matches: List[Dict]
    ) -> str:
        """Sonuçlar için açıklama üret"""
        if not matches:
            return "Belirtilen kriterlere uygun dizayn bulunamadı."

        # Basit fallback açıklama
        fallback = self._generate_simple_explanation(extracted_params, matches)

        try:
            async with httpx.AsyncClient() as client:
                prompt = self._build_explanation_prompt(user_query, extracted_params, matches)

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 300
                        }
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    explanation = result.get("response", "").strip()
                    if explanation:
                        return explanation

        except Exception as e:
            print(f"Ollama explanation error: {e}")

        return fallback

    def _generate_simple_explanation(
        self,
        extracted_params: Dict,
        matches: List[Dict]
    ) -> str:
        """Basit açıklama üret (LLM olmadan)"""
        if not matches:
            return "Kriterlere uygun dizayn bulunamadı."

        best = matches[0]
        score = best["similarity_score"] * 100

        param_list = []
        if "rating_kva" in extracted_params:
            param_list.append(f"{extracted_params['rating_kva']} kVA")
        if "high_voltage_v" in extracted_params:
            param_list.append(f"{extracted_params['high_voltage_v']}V YG")
        if "low_voltage_v" in extracted_params:
            param_list.append(f"{extracted_params['low_voltage_v']}V AG")

        params_str = ", ".join(param_list) if param_list else "belirtilen parametreler"

        return (
            f"{params_str} için {len(matches)} adet uygun dizayn bulundu. "
            f"En yakın eşleşme: {best['design_number']} (%{score:.1f} benzerlik)."
        )
