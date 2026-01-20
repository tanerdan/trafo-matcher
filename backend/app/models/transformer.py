from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TransformerSpecs(BaseModel):
    """Trafo temel spesifikasyonları - Excel'den parse edilen veriler

    Alan adlandırma kuralı:
    - input_ prefix: Input specifications sheet'inden gelen veriler
    - output_ prefix: Output sheet'inden gelen veriler
    """

    # === META BİLGİLER ===
    id: Optional[int] = None
    design_number: Optional[str] = None
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # === INPUT SPECIFICATIONS SHEET ===

    # Güç ve Gerilim
    input_rating_kva: Optional[float] = None              # #1 Rating
    input_onaf_rating_kva: Optional[float] = None         # #2 ONAF Rating
    input_high_voltage_v: Optional[float] = None          # #3 High voltage
    input_low_voltage_v: Optional[float] = None           # #4 Low voltage

    # Bağlantı
    input_connection_hv: Optional[str] = None             # #5 Connection HV (Triangle/Star)
    input_connection_lv: Optional[str] = None             # #6 Connection LV (Triangle/Star)

    # Elektriksel
    input_frequency_hz: Optional[float] = None            # #7 Frequency
    input_no_load_loss_w: Optional[float] = None          # #8 No-load losses (Garanti)
    input_load_loss_w: Optional[float] = None             # #9 Load losses (Garanti)
    input_impedance_percent: Optional[float] = None       # #11 Ucc (%)
    input_no_load_current_percent: Optional[float] = None # #12 No-load current (%)
    input_clock_number: Optional[int] = None              # #13 Clock number

    # Soğutma ve Malzeme
    input_cooling_type: Optional[str] = None              # #14 Cooling Type (ONAN/ONAF/OFAF)
    input_lv_material: Optional[str] = None               # #15 LV material (al/cu)
    input_hv_material: Optional[str] = None               # #16 HV material (al/cu)
    input_lv_winding_type: Optional[str] = None           # #17 Low voltage winding (Foil/Layer)
    input_hv_wire_type: Optional[str] = None              # #18 HV wire type
    input_lv_wire_type: Optional[str] = None              # #19 LV wire type
    input_core_shape: Optional[str] = None                # #20 core shape (obround/round)

    # Sıcaklık
    input_ambient_temp_c: Optional[float] = None          # #21 Ambient temperature
    input_top_oil_rise_k: Optional[float] = None          # #22 Top oil
    input_winding_rise_k: Optional[float] = None          # #23 Winding
    input_hotspot_k: Optional[float] = None               # #24 hotspot

    # === OUTPUT SHEET ===

    # Bağlantı
    output_vector_group: Optional[str] = None             # #40 Connection symbol (Dyn11 vb.)
    output_voltage_lv_v: Optional[float] = None           # #41 Voltage LV
    output_voltage_hv_v: Optional[float] = None           # #42 Voltage HV

    # Nüve
    output_core_diameter_mm: Optional[float] = None       # #49 Core diameter
    output_core_section_cm2: Optional[float] = None       # #50 Core section (cm²)
    output_core_weight_kg: Optional[float] = None         # #51 Core Weight (kg)
    output_core_material: Optional[str] = None            # #52 Core Material
    output_induction_tesla: Optional[float] = None        # #53 Induction (Tesla)

    # Hesaplanan Kayıplar
    output_no_load_loss_w: Optional[float] = None         # #54 No load losses (Hesaplanan)
    output_no_load_current_percent: Optional[float] = None # #55 No load current (%)
    output_load_loss_w: Optional[float] = None            # #56 total load losses
    output_impedance_percent: Optional[float] = None      # #58 Impedance Ucc (Hesaplanan)

    # Verimlilik
    output_pei: Optional[float] = None                    # #59 PEI
    output_efficiency_percent: Optional[float] = None     # #60 efficiency at 100%
    output_sound_power_db: Optional[float] = None         # #61 Sound Power dB(A)

    # Sıcaklık (Hesaplanan)
    output_top_oil_rise_k: Optional[float] = None         # #62 Top oil (temp rise)
    output_winding_temp_hv_k: Optional[float] = None      # #63 Winding temp (HV)
    output_winding_temp_lv_k: Optional[float] = None      # #64 Winding temp (LV)
    output_hotspot_k: Optional[float] = None              # #65 hotspot

    # Ağırlıklar
    output_weight_lv_kg: Optional[float] = None           # #66 Weight LV (kg)
    output_weight_hv_kg: Optional[float] = None           # #67 Weight HV (kg)
    output_total_weight_kg: Optional[float] = None        # #68 Total (kg)
    output_oil_volume_l: Optional[float] = None           # #69 Oil volume (L)

    # Tank Boyutları
    output_tank_length_mm: Optional[float] = None         # #70 Inner Length
    output_tank_width_mm: Optional[float] = None          # #71 Inner Width
    output_tank_height_mm: Optional[float] = None         # #72 final height

    # AG Sargı Detayları
    output_foil_height_mm: Optional[float] = None         # #73 Foil Height (mm)
    output_foil_thickness_mm: Optional[float] = None      # #74 Foil Thickness (mm)
    output_turns_lv: Optional[int] = None                 # #75 Number of Turns LV
    output_turns_hv: Optional[int] = None                 # #76 Number of turns HV

    # Sargı Çapları
    output_inner_diameter_lv_mm: Optional[float] = None   # #77 Inner diameter LV
    output_outer_diameter_lv_mm: Optional[float] = None   # #78 Outer diameter LV
    output_inner_diameter_hv_mm: Optional[float] = None   # #79 Inner diameter HV
    output_outer_diameter_hv_mm: Optional[float] = None   # #80 Outer diameter HV

    # Akımlar
    output_phase_current_lv_a: Optional[float] = None     # #81 Phase current LV (A)
    output_phase_current_hv_a: Optional[float] = None     # #82 Phase current HV (A)
    output_current_density_lv: Optional[float] = None     # #83 Current density LV (A/mm²)
    output_current_density_hv: Optional[float] = None     # #84 Current density HV (A/mm²)

    # Diğer
    output_volts_per_turn: Optional[float] = None         # #85 Volts per turn
    output_cost_dollar: Optional[float] = None            # #86 Cost Dollar

    # === UYUMLULUK İÇİN ESKİ ALAN İSİMLERİ (property olarak) ===
    @property
    def rating_kva(self) -> Optional[float]:
        return self.input_rating_kva

    @property
    def high_voltage_v(self) -> Optional[float]:
        return self.input_high_voltage_v

    @property
    def low_voltage_v(self) -> Optional[float]:
        return self.input_low_voltage_v

    @property
    def vector_group(self) -> Optional[str]:
        return self.output_vector_group

    @property
    def no_load_loss_w(self) -> Optional[float]:
        return self.output_no_load_loss_w or self.input_no_load_loss_w

    @property
    def load_loss_w(self) -> Optional[float]:
        return self.output_load_loss_w or self.input_load_loss_w

    @property
    def impedance_percent(self) -> Optional[float]:
        return self.output_impedance_percent or self.input_impedance_percent

    @property
    def cooling_type(self) -> Optional[str]:
        return self.input_cooling_type

    @property
    def frequency_hz(self) -> Optional[float]:
        return self.input_frequency_hz

    @property
    def hv_material(self) -> Optional[str]:
        return self.input_hv_material

    @property
    def lv_material(self) -> Optional[str]:
        return self.input_lv_material


class TransformerQuery(BaseModel):
    """Kullanıcıdan gelen trafo arama sorgusu"""
    query: str
    max_results: int = 5


class FormSearchQuery(BaseModel):
    """Form tabanlı arama sorgusu - LLM gerektirmez"""
    rating_kva: Optional[float] = None
    high_voltage_v: Optional[float] = None
    low_voltage_v: Optional[float] = None
    vector_group: Optional[str] = None
    cooling_type: Optional[str] = None
    hv_material: Optional[str] = None
    lv_material: Optional[str] = None
    impedance_percent: Optional[float] = None  # Ucc (%)
    max_no_load_loss_w: Optional[float] = None
    max_load_loss_w: Optional[float] = None
    max_results: int = 10


class TransformerMatch(BaseModel):
    """Eşleşen trafo sonucu"""
    design_number: str
    file_path: str
    similarity_score: float
    specs: TransformerSpecs
    match_details: dict

    class Config:
        # Property'lerin serialize edilmesi için
        from_attributes = True


class SearchResponse(BaseModel):
    """Arama sonuç yanıtı"""
    query: str
    extracted_params: dict
    matches: List[TransformerMatch]
    explanation: str


class DesignStats(BaseModel):
    """Veritabanı istatistikleri"""
    total_designs: int
    rating_range: tuple
    voltage_range: tuple
    vector_groups: List[str]
    cooling_types: List[str]
    materials: dict
