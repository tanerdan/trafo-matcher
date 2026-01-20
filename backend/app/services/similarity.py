import numpy as np
from typing import List, Dict, Tuple, Optional
from ..models.transformer import TransformerSpecs, TransformerMatch


class SimilarityEngine:
    """Trafo parametreleri arasında benzerlik hesaplayan motor"""

    # Parametre ağırlıkları (önem sırasına göre)
    WEIGHTS = {
        "rating_kva": 1.0,          # En önemli - güç
        "high_voltage_v": 0.9,       # Çok önemli - YG gerilim
        "low_voltage_v": 0.9,        # Çok önemli - AG gerilim
        "vector_group": 0.8,         # Önemli - bağlantı grubu
        "no_load_loss_w": 0.7,       # Önemli - boşta kayıp
        "load_loss_w": 0.7,          # Önemli - yük kaybı
        "impedance_percent": 0.6,    # Orta önem - empedans
        "cooling_type": 0.5,         # Orta önem - soğutma
        "frequency_hz": 0.5,         # Orta önem - frekans
        "lv_material": 0.4,          # Düşük önem - malzeme
        "hv_material": 0.4,
        "core_material": 0.3,
    }

    # Tolerans değerleri (yüzde olarak)
    TOLERANCES = {
        "rating_kva": 0.05,          # %5 tolerans (sıkı)
        "high_voltage_v": 0.05,      # %5 tolerans
        "low_voltage_v": 0.05,       # %5 tolerans
        "no_load_loss_w": 0.15,
        "load_loss_w": 0.15,
        "impedance_percent": 0.1,
        "frequency_hz": 0.0,         # Tam eşleşme
    }

    def __init__(self):
        pass

    def calculate_numeric_similarity(
        self,
        value1: Optional[float],
        value2: Optional[float],
        tolerance: float = 0.1
    ) -> float:
        """İki sayısal değer arasındaki benzerliği hesapla (0-1 arası)"""
        if value1 is None or value2 is None:
            return 0.5  # Bilinmeyen değerler için nötr skor

        # String'den float'a dönüştür (birim temizleme dahil)
        import re
        def extract_number(val):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                # "11000V", "50Hz", "100kVA" gibi string'lerden sayı çıkar
                match = re.search(r'[-+]?\d*\.?\d+', val.replace(',', '.'))
                if match:
                    return float(match.group())
            return None

        v1 = extract_number(value1)
        v2 = extract_number(value2)

        if v1 is None or v2 is None:
            return 0.0

        if v1 == 0 and v2 == 0:
            return 1.0

        if v1 == 0 or v2 == 0:
            return 0.0

        # Yüzde fark hesapla
        diff = abs(v1 - v2) / max(abs(v1), abs(v2))

        # Tam eşleşme veya %5 içinde: 100%
        if diff <= 0.05:
            return 1.0

        # %5-10 fark: 90%
        if diff <= 0.10:
            return 0.9

        # %10-20 fark: 40%
        if diff <= 0.20:
            return 0.4

        # %20+ fark: 0%
        return 0.0

    def calculate_string_similarity(
        self,
        value1: Optional[str],
        value2: Optional[str]
    ) -> float:
        """İki string değer arasındaki benzerliği hesapla"""
        if value1 is None or value2 is None:
            return 0.5

        v1 = value1.lower().strip()
        v2 = value2.lower().strip()

        if v1 == v2:
            return 1.0

        # Kısmi eşleşme (biri diğerini içeriyor)
        if v1 in v2 or v2 in v1:
            return 0.7

        return 0.0

    def calculate_vector_group_similarity(
        self,
        vg1: Optional[str],
        vg2: Optional[str]
    ) -> float:
        """Vektör grubu benzerliği (Dyn11, Yyn0, vb.)

        Kurallar:
        - Tam eşleşme: 100%
        - Saat numarası hariç eşleşme: 80% (örn: Dyn5 vs Dyn11)
        - Diğer: 0%
        """
        if vg1 is None or vg2 is None:
            return 0.5

        v1 = vg1.lower().strip()
        v2 = vg2.lower().strip()

        # Tam eşleşme
        if v1 == v2:
            return 1.0

        # Saat numarasını ayır (sondaki rakamlar)
        import re
        match1 = re.match(r'^([a-z]+)(\d*)$', v1)
        match2 = re.match(r'^([a-z]+)(\d*)$', v2)

        if match1 and match2:
            base1 = match1.group(1)  # "dyn"
            base2 = match2.group(1)  # "dyn"

            # Bağlantı tipi aynı, sadece saat numarası farklı
            if base1 == base2:
                return 0.8

        # Diğer tüm durumlar
        return 0.0

    def calculate_similarity(
        self,
        query_specs: Dict,
        design_specs: TransformerSpecs
    ) -> Tuple[float, Dict]:
        """
        Sorgu parametreleri ile bir dizayn arasındaki benzerliği hesapla

        Returns:
            Tuple[float, Dict]: (benzerlik_skoru, detaylar)
        """
        total_score = 0.0
        total_weight = 0.0
        match_details = {}

        for param, weight in self.WEIGHTS.items():
            query_value = query_specs.get(param)
            design_value = getattr(design_specs, param, None)

            # Sorguda bu parametre yoksa atla
            if query_value is None:
                continue

            tolerance = self.TOLERANCES.get(param, 0.15)

            # Parametre tipine göre benzerlik hesapla
            if param in ["vector_group"]:
                score = self.calculate_vector_group_similarity(query_value, design_value)
            elif param in ["cooling_type", "lv_material", "hv_material", "core_material", "connection_hv", "connection_lv"]:
                score = self.calculate_string_similarity(query_value, design_value)
            else:
                score = self.calculate_numeric_similarity(query_value, design_value, tolerance)

            weighted_score = score * weight
            total_score += weighted_score
            total_weight += weight

            match_details[param] = {
                "query": query_value,
                "design": design_value,
                "score": round(score, 3),
                "weighted_score": round(weighted_score, 3)
            }

        # Normalize et
        final_score = total_score / total_weight if total_weight > 0 else 0.0

        return final_score, match_details

    def find_similar_designs(
        self,
        query_specs: Dict,
        all_designs: List[TransformerSpecs],
        max_results: int = 5,
        min_score: float = 0.3
    ) -> List[TransformerMatch]:
        """
        Verilen parametrelere en yakın dizaynları bul

        Args:
            query_specs: Aranan trafo parametreleri
            all_designs: Tüm dizayn listesi
            max_results: Maksimum sonuç sayısı
            min_score: Minimum benzerlik skoru

        Returns:
            List[TransformerMatch]: Sıralı eşleşme listesi
        """
        matches = []

        for design in all_designs:
            score, details = self.calculate_similarity(query_specs, design)

            if score >= min_score:
                matches.append(TransformerMatch(
                    design_number=design.design_number or "Unknown",
                    file_path=design.file_path or "",
                    similarity_score=round(score, 4),
                    specs=design,
                    match_details=details
                ))

        # Skora göre sırala
        matches.sort(key=lambda x: x.similarity_score, reverse=True)

        return matches[:max_results]
