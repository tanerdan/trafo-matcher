import pandas as pd
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from ..models.transformer import TransformerSpecs


class ExcelParser:
    """Excel trafo dizayn dosyalarını parse eden servis

    Sadece geçerli dosyaları parse eder:
    - .xlsx uzantılı dosyalar
    - "Input specifications" VE "Output" sheet'leri olan dosyalar
    """

    def __init__(self, designs_directory: str):
        self.designs_directory = Path(designs_directory)
        self.designs_cache: List[TransformerSpecs] = []

    def find_excel_files(self) -> List[Path]:
        """Dizindeki tüm Excel dosyalarını bul"""
        excel_files = []
        for pattern in ["**/*.xlsx", "**/*.xlsm"]:
            excel_files.extend(self.designs_directory.glob(pattern))
        # Geçici dosyaları (~$) filtrele
        excel_files = [f for f in excel_files if not f.name.startswith("~$")]
        return excel_files

    def find_valid_design_files(self) -> List[Path]:
        """Sadece geçerli dizayn dosyalarını bul (Input specifications + Output sheet'leri olan)"""
        valid_files = []
        excel_files = self.find_excel_files()

        for file_path in excel_files:
            try:
                xl = pd.ExcelFile(file_path)
                sheet_names = xl.sheet_names
                if "Input specifications" in sheet_names and "Output" in sheet_names:
                    valid_files.append(file_path)
            except Exception as e:
                print(f"Dosya kontrol edilemedi {file_path}: {e}")
                continue

        return valid_files

    def _safe_float(self, value: Any) -> Optional[float]:
        """Güvenli float dönüşümü"""
        if value is None or pd.isna(value):
            return None
        try:
            # String içindeki sayıyı çıkar
            if isinstance(value, str):
                # "100 kVA" -> 100, "11000 V" -> 11000
                match = re.search(r"[-+]?\d*\.?\d+", value.replace(",", "."))
                if match:
                    return float(match.group())
                return None
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Güvenli int dönüşümü"""
        float_val = self._safe_float(value)
        if float_val is not None:
            return int(float_val)
        return None

    def _safe_str(self, value: Any) -> Optional[str]:
        """Güvenli string dönüşümü"""
        if value is None or pd.isna(value):
            return None
        return str(value).strip()

    def _find_cell_value(
        self, df: pd.DataFrame, search_text: str, offset_col: int = 1, offset_row: int = 0,
        exact_match: bool = False
    ) -> Any:
        """DataFrame'de belirli bir metni ara ve belirtilen offset'teki değeri döndür

        Args:
            df: DataFrame
            search_text: Aranacak metin
            offset_col: Sütun offset'i (varsayılan 1 = sağdaki hücre)
            offset_row: Satır offset'i (varsayılan 0 = aynı satır)
            exact_match: True ise tam eşleşme arar (strip edilmiş hali)
        """
        for i in range(len(df)):
            for j in range(len(df.columns)):
                cell = df.iloc[i, j]
                if isinstance(cell, str):
                    cell_lower = cell.lower().strip()
                    search_lower = search_text.lower().strip()

                    if exact_match:
                        match = cell_lower == search_lower
                    else:
                        match = search_lower in cell_lower

                    if match:
                        target_row = i + offset_row
                        target_col = j + offset_col
                        # Sınırları kontrol et
                        if target_row < len(df) and target_col < len(df.columns) and target_col >= 0:
                            return df.iloc[target_row, target_col]
        return None

    def parse_excel_file(self, file_path: Path) -> Optional[TransformerSpecs]:
        """Tek bir Excel dosyasını parse et - 56 alan"""
        try:
            # Sheet isimlerini kontrol et
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names

            # Geçerli dosya kontrolü
            if "Input specifications" not in sheet_names or "Output" not in sheet_names:
                print(f"Geçersiz dosya (gerekli sheet yok): {file_path}")
                return None

            specs = TransformerSpecs(
                file_path=str(file_path),
                design_number=file_path.stem
            )

            # Input specifications sheet'ini oku
            df_input = pd.read_excel(file_path, sheet_name="Input specifications", header=None)
            specs = self._parse_input_specs(df_input, specs)

            # Output sheet'ini oku
            df_output = pd.read_excel(file_path, sheet_name="Output", header=None)
            specs = self._parse_output(df_output, specs)

            return specs

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def _parse_input_specs(
        self, df: pd.DataFrame, specs: TransformerSpecs
    ) -> TransformerSpecs:
        """Input specifications sheet'ini parse et - 24 alan"""

        # === GÜÇ VE GERİLİM ===
        # #1 Rating (kVA)
        specs.input_rating_kva = self._safe_float(self._find_cell_value(df, "Rating"))

        # #2 ONAF Rating
        specs.input_onaf_rating_kva = self._safe_float(self._find_cell_value(df, "ONAF Rating"))

        # #3 High Voltage
        specs.input_high_voltage_v = self._safe_float(
            self._find_cell_value(df, "High voltage", exact_match=True)
        )

        # #4 Low Voltage
        specs.input_low_voltage_v = self._safe_float(
            self._find_cell_value(df, "Low voltage", exact_match=True)
        )

        # === BAĞLANTI ===
        # #5 Connection HV
        specs.input_connection_hv = self._safe_str(self._find_cell_value(df, "Connection HV"))

        # #6 Connection LV
        specs.input_connection_lv = self._safe_str(self._find_cell_value(df, "Connection LV"))

        # === ELEKTRİKSEL ===
        # #7 Frequency
        specs.input_frequency_hz = self._safe_float(self._find_cell_value(df, "Frequency"))

        # #8 No-load losses (Garanti değeri)
        specs.input_no_load_loss_w = self._safe_float(
            self._find_cell_value(df, "No-load losses", exact_match=True)
        )

        # #9 Load losses (Garanti değeri)
        specs.input_load_loss_w = self._safe_float(
            self._find_cell_value(df, "Load losses", exact_match=True)
        )

        # #11 Ucc (Empedans %)
        specs.input_impedance_percent = self._safe_float(self._find_cell_value(df, "Ucc"))

        # #12 No-load current (%)
        specs.input_no_load_current_percent = self._safe_float(
            self._find_cell_value(df, "No-load current")
        )

        # #13 Clock number
        specs.input_clock_number = self._safe_int(self._find_cell_value(df, "Clock number"))

        # === SOĞUTMA VE MALZEME ===
        # #14 Cooling Type (başlık altındaki satırda)
        specs.input_cooling_type = self._safe_str(
            self._find_cell_value(df, "Cooilng Type", offset_col=0, offset_row=1)
        )
        if not specs.input_cooling_type:
            specs.input_cooling_type = self._safe_str(
                self._find_cell_value(df, "Cooling Type", offset_col=0, offset_row=1)
            )

        # #15 LV material
        specs.input_lv_material = self._safe_str(self._find_cell_value(df, "LV material"))

        # #16 HV material
        specs.input_hv_material = self._safe_str(self._find_cell_value(df, "HV material"))

        # #17 Low voltage winding (Foil/Layer)
        specs.input_lv_winding_type = self._safe_str(
            self._find_cell_value(df, "Low voltage winding")
        )

        # #18 HV wire type
        specs.input_hv_wire_type = self._safe_str(self._find_cell_value(df, "HV wire type"))

        # #19 LV wire type
        specs.input_lv_wire_type = self._safe_str(self._find_cell_value(df, "LV wire type"))

        # #20 core shape
        specs.input_core_shape = self._safe_str(self._find_cell_value(df, "core shape"))

        # === SICAKLIK ===
        # #21 Ambient temperature
        specs.input_ambient_temp_c = self._safe_float(
            self._find_cell_value(df, "Ambient temperature")
        )

        # #22 Top oil
        specs.input_top_oil_rise_k = self._safe_float(self._find_cell_value(df, "Top oil"))

        # #23 Winding
        specs.input_winding_rise_k = self._safe_float(self._find_cell_value(df, "Winding"))

        # #24 hotspot
        specs.input_hotspot_k = self._safe_float(
            self._find_cell_value(df, "hotspot", exact_match=True)
        )

        return specs

    def _parse_output(self, df: pd.DataFrame, specs: TransformerSpecs) -> TransformerSpecs:
        """Output sheet'ini parse et - 32 alan"""

        # === BAĞLANTI ===
        # #40 Connection symbol (Vector Group) - başlık altındaki satırda
        specs.output_vector_group = self._safe_str(
            self._find_cell_value(df, "Connection symbol", offset_col=0, offset_row=1)
        )

        # #41 Voltage LV
        specs.output_voltage_lv_v = self._safe_float(
            self._find_cell_value(df, "Voltage LV", exact_match=False)
        )

        # #42 Voltage HV
        specs.output_voltage_hv_v = self._safe_float(
            self._find_cell_value(df, "Voltage HV", exact_match=False)
        )

        # === NÜVE ===
        # #49 Core diameter
        specs.output_core_diameter_mm = self._safe_float(
            self._find_cell_value(df, "Core diameter")
        )

        # #50 Core section (cm²)
        specs.output_core_section_cm2 = self._safe_float(
            self._find_cell_value(df, "Core section")
        )

        # #51 Core Weight (kg)
        specs.output_core_weight_kg = self._safe_float(self._find_cell_value(df, "Core Weight"))

        # #52 Core Material
        specs.output_core_material = self._safe_str(self._find_cell_value(df, "Core Material"))

        # #53 Induction (Tesla)
        specs.output_induction_tesla = self._safe_float(self._find_cell_value(df, "Induction"))

        # === HESAPLANAN KAYIPLAR ===
        # #54 No load losses (Hesaplanan)
        specs.output_no_load_loss_w = self._safe_float(
            self._find_cell_value(df, "No load losses")
        )

        # #55 No load current (%)
        specs.output_no_load_current_percent = self._safe_float(
            self._find_cell_value(df, "No load current")
        )

        # #56 total load losses
        specs.output_load_loss_w = self._safe_float(
            self._find_cell_value(df, "total load losses")
        )

        # #58 Impedance Ucc (Hesaplanan)
        specs.output_impedance_percent = self._safe_float(
            self._find_cell_value(df, "Impedance Ucc")
        )

        # === VERİMLİLİK ===
        # #59 PEI
        specs.output_pei = self._safe_float(self._find_cell_value(df, "PEI"))

        # #60 efficiency at 100%
        specs.output_efficiency_percent = self._safe_float(
            self._find_cell_value(df, "efficiency at 100")
        )

        # #61 Sound Power dB(A)
        specs.output_sound_power_db = self._safe_float(
            self._find_cell_value(df, "Sound Power")
        )

        # === SICAKLIK (HESAPLANAN) ===
        # #62 Top oil (temp rise)
        specs.output_top_oil_rise_k = self._safe_float(
            self._find_cell_value(df, "Top oil", exact_match=False)
        )

        # #63 Winding temp (HV)
        specs.output_winding_temp_hv_k = self._safe_float(
            self._find_cell_value(df, "Winding temp (HV)")
        )
        if not specs.output_winding_temp_hv_k:
            specs.output_winding_temp_hv_k = self._safe_float(
                self._find_cell_value(df, "Winding temperature HV")
            )

        # #64 Winding temp (LV)
        specs.output_winding_temp_lv_k = self._safe_float(
            self._find_cell_value(df, "Winding temp (LV)")
        )
        if not specs.output_winding_temp_lv_k:
            specs.output_winding_temp_lv_k = self._safe_float(
                self._find_cell_value(df, "Winding temperature LV")
            )

        # #65 hotspot (output)
        specs.output_hotspot_k = self._safe_float(
            self._find_cell_value(df, "hotspot", exact_match=True)
        )

        # === AĞIRLIKLAR ===
        # #66 Weight LV (kg)
        specs.output_weight_lv_kg = self._safe_float(self._find_cell_value(df, "Weight LV"))

        # #67 Weight HV (kg)
        specs.output_weight_hv_kg = self._safe_float(self._find_cell_value(df, "Weight HV"))

        # #68 Total (kg)
        specs.output_total_weight_kg = self._safe_float(self._find_cell_value(df, "Total (kg)"))

        # #69 Oil volume (L)
        specs.output_oil_volume_l = self._safe_float(self._find_cell_value(df, "Oil volume"))

        # === TANK BOYUTLARI ===
        # #70 Inner Length
        specs.output_tank_length_mm = self._safe_float(self._find_cell_value(df, "Inner Length"))

        # #71 Inner Width
        specs.output_tank_width_mm = self._safe_float(self._find_cell_value(df, "Inner Widht"))
        if not specs.output_tank_width_mm:
            specs.output_tank_width_mm = self._safe_float(
                self._find_cell_value(df, "Inner Width")
            )

        # #72 final height
        specs.output_tank_height_mm = self._safe_float(self._find_cell_value(df, "final height"))

        # === AG SARGI DETAYLARI ===
        # #73 Foil Height (mm)
        specs.output_foil_height_mm = self._safe_float(self._find_cell_value(df, "Foil Height"))

        # #74 Foil Thickness (mm)
        specs.output_foil_thickness_mm = self._safe_float(
            self._find_cell_value(df, "Foil Thickness")
        )

        # #75 Number of Turns LV
        specs.output_turns_lv = self._safe_int(self._find_cell_value(df, "Number of Turns LV"))
        if not specs.output_turns_lv:
            specs.output_turns_lv = self._safe_int(
                self._find_cell_value(df, "Number of turns LV")
            )

        # #76 Number of turns HV
        specs.output_turns_hv = self._safe_int(self._find_cell_value(df, "Number of turns HV"))

        # === SARGI ÇAPLARI ===
        # #77 Inner diameter LV
        specs.output_inner_diameter_lv_mm = self._safe_float(
            self._find_cell_value(df, "Inner diameter LV")
        )

        # #78 Outer diameter LV
        specs.output_outer_diameter_lv_mm = self._safe_float(
            self._find_cell_value(df, "Outer diameter LV")
        )

        # #79 Inner diameter HV
        specs.output_inner_diameter_hv_mm = self._safe_float(
            self._find_cell_value(df, "Inner diameter HV")
        )

        # #80 Outer diameter HV
        specs.output_outer_diameter_hv_mm = self._safe_float(
            self._find_cell_value(df, "Outer diameter HV")
        )

        # === AKIMLAR ===
        # #81 Phase current LV (A)
        specs.output_phase_current_lv_a = self._safe_float(
            self._find_cell_value(df, "Phase current LV")
        )

        # #82 Phase current HV (A)
        specs.output_phase_current_hv_a = self._safe_float(
            self._find_cell_value(df, "Phase current HV")
        )

        # #83 Current density LV
        specs.output_current_density_lv = self._safe_float(
            self._find_cell_value(df, "Current density LV")
        )

        # #84 Current density HV
        specs.output_current_density_hv = self._safe_float(
            self._find_cell_value(df, "Current density HV")
        )

        # === DİĞER ===
        # #85 Volts per turn
        specs.output_volts_per_turn = self._safe_float(
            self._find_cell_value(df, "Volts per turn")
        )

        # #86 Cost Dollar
        specs.output_cost_dollar = self._safe_float(self._find_cell_value(df, "Cost Dollar"))
        if not specs.output_cost_dollar:
            specs.output_cost_dollar = self._safe_float(self._find_cell_value(df, "Cost"))

        return specs

    def load_all_designs(self) -> List[TransformerSpecs]:
        """Tüm geçerli dizaynları yükle ve cache'le"""
        valid_files = self.find_valid_design_files()
        self.designs_cache = []

        for file_path in valid_files:
            specs = self.parse_excel_file(file_path)
            if specs and specs.input_rating_kva:  # En azından rating olmalı
                self.designs_cache.append(specs)

        print(f"Loaded {len(self.designs_cache)} transformer designs")
        return self.designs_cache

    def get_all_designs(self) -> List[TransformerSpecs]:
        """Cache'deki tüm dizaynları döndür"""
        if not self.designs_cache:
            self.load_all_designs()
        return self.designs_cache

    def refresh_designs(self) -> List[TransformerSpecs]:
        """Dizaynları yeniden yükle"""
        return self.load_all_designs()

    def parse_single_file(self, file_path: str) -> Optional[TransformerSpecs]:
        """Tek bir dosyayı parse et (n8n webhook için)"""
        return self.parse_excel_file(Path(file_path))
