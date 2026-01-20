"""Veritabanı CRUD operasyonları servisi"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from .database import get_connection, init_database
from ..models.transformer import TransformerSpecs


# TransformerSpecs model alanları (meta hariç)
DESIGN_FIELDS = [
    # Input specifications (24 alan)
    "input_rating_kva", "input_onaf_rating_kva", "input_high_voltage_v", "input_low_voltage_v",
    "input_connection_hv", "input_connection_lv",
    "input_frequency_hz", "input_no_load_loss_w", "input_load_loss_w",
    "input_impedance_percent", "input_no_load_current_percent", "input_clock_number",
    "input_cooling_type", "input_lv_material", "input_hv_material",
    "input_lv_winding_type", "input_hv_wire_type", "input_lv_wire_type", "input_core_shape",
    "input_ambient_temp_c", "input_top_oil_rise_k", "input_winding_rise_k", "input_hotspot_k",

    # Output sheet (32 alan)
    "output_vector_group", "output_voltage_lv_v", "output_voltage_hv_v",
    "output_core_diameter_mm", "output_core_section_cm2", "output_core_weight_kg",
    "output_core_material", "output_induction_tesla",
    "output_no_load_loss_w", "output_no_load_current_percent", "output_load_loss_w",
    "output_impedance_percent",
    "output_pei", "output_efficiency_percent", "output_sound_power_db",
    "output_top_oil_rise_k", "output_winding_temp_hv_k", "output_winding_temp_lv_k", "output_hotspot_k",
    "output_weight_lv_kg", "output_weight_hv_kg", "output_total_weight_kg", "output_oil_volume_l",
    "output_tank_length_mm", "output_tank_width_mm", "output_tank_height_mm",
    "output_foil_height_mm", "output_foil_thickness_mm", "output_turns_lv", "output_turns_hv",
    "output_inner_diameter_lv_mm", "output_outer_diameter_lv_mm",
    "output_inner_diameter_hv_mm", "output_outer_diameter_hv_mm",
    "output_phase_current_lv_a", "output_phase_current_hv_a",
    "output_current_density_lv", "output_current_density_hv",
    "output_volts_per_turn", "output_cost_dollar"
]


class DatabaseService:
    """Veritabanı operasyonları servisi"""

    def __init__(self):
        init_database()

    def _row_to_specs(self, row) -> TransformerSpecs:
        """SQLite Row'u TransformerSpecs'e dönüştür"""
        data = dict(row)
        # datetime string'leri datetime objesine çevir
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return TransformerSpecs(**data)

    def _specs_to_dict(self, specs: TransformerSpecs) -> Dict[str, Any]:
        """TransformerSpecs'i veritabanı dict'ine dönüştür"""
        result = {
            "design_number": specs.design_number,
            "file_path": specs.file_path,
        }
        for field in DESIGN_FIELDS:
            result[field] = getattr(specs, field, None)
        return result

    # === CRUD Operasyonları ===

    def get_all_designs(self) -> List[TransformerSpecs]:
        """Tüm dizaynları getir"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM designs ORDER BY input_rating_kva")
            rows = cursor.fetchall()
            return [self._row_to_specs(row) for row in rows]

    def get_design_by_id(self, design_id: int) -> Optional[TransformerSpecs]:
        """ID ile dizayn getir"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM designs WHERE id = ?", (design_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_specs(row)
            return None

    def get_design_by_number(self, design_number: str) -> Optional[TransformerSpecs]:
        """Dizayn numarası ile getir"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM designs WHERE design_number = ?",
                (design_number,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_specs(row)
            return None

    def add_design(self, specs: TransformerSpecs) -> int:
        """Yeni dizayn ekle, ID döndür"""
        data = self._specs_to_dict(specs)
        fields = list(data.keys())
        placeholders = ", ".join(["?" for _ in fields])
        field_names = ", ".join(fields)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO designs ({field_names}) VALUES ({placeholders})",
                [data[f] for f in fields]
            )
            conn.commit()
            return cursor.lastrowid

    def update_design(self, design_id: int, specs: TransformerSpecs) -> bool:
        """Dizayn güncelle"""
        data = self._specs_to_dict(specs)
        data["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [design_id]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE designs SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0

    def upsert_design(self, specs: TransformerSpecs) -> int:
        """Dizayn ekle veya güncelle (design_number'a göre)"""
        existing = self.get_design_by_number(specs.design_number)
        if existing:
            self.update_design(existing.id, specs)
            return existing.id
        else:
            return self.add_design(specs)

    def delete_design(self, design_id: int) -> bool:
        """Dizayn sil"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM designs WHERE id = ?", (design_id,))
            conn.commit()
            return cursor.rowcount > 0

    def delete_all_designs(self) -> int:
        """Tüm dizaynları sil"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM designs")
            conn.commit()
            return cursor.rowcount

    # === Arama ve Filtreleme ===

    def search_designs(
        self,
        rating_kva: Optional[float] = None,
        high_voltage_v: Optional[float] = None,
        low_voltage_v: Optional[float] = None,
        vector_group: Optional[str] = None,
        cooling_type: Optional[str] = None,
        hv_material: Optional[str] = None,
        lv_material: Optional[str] = None,
        limit: int = 100
    ) -> List[TransformerSpecs]:
        """Filtrelenmiş arama - tam eşleşme değil, benzerlik için kullanılır"""
        with get_connection() as conn:
            cursor = conn.cursor()
            # Tüm kayıtları getir, Python'da skorlama yapılacak
            cursor.execute("SELECT * FROM designs")
            rows = cursor.fetchall()
            return [self._row_to_specs(row) for row in rows]

    def get_distinct_values(self, field: str) -> List[str]:
        """Bir alanın tüm benzersiz değerlerini getir (dropdown için)"""
        if field not in DESIGN_FIELDS and field not in ["output_vector_group", "input_cooling_type"]:
            return []

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT DISTINCT {field} FROM designs WHERE {field} IS NOT NULL ORDER BY {field}")
            return [row[0] for row in cursor.fetchall()]

    # === İstatistikler ===

    def get_stats(self) -> Dict[str, Any]:
        """Veritabanı istatistiklerini getir"""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Toplam sayı
            cursor.execute("SELECT COUNT(*) FROM designs")
            total = cursor.fetchone()[0]

            # Rating aralığı
            cursor.execute(
                "SELECT MIN(input_rating_kva), MAX(input_rating_kva) FROM designs"
            )
            rating_range = cursor.fetchone()

            # Gerilim aralığı
            cursor.execute(
                "SELECT MIN(input_high_voltage_v), MAX(input_high_voltage_v) FROM designs"
            )
            hv_range = cursor.fetchone()

            # Vektör grupları
            cursor.execute(
                "SELECT DISTINCT output_vector_group FROM designs WHERE output_vector_group IS NOT NULL"
            )
            vector_groups = [row[0] for row in cursor.fetchall()]

            # Soğutma tipleri
            cursor.execute(
                "SELECT DISTINCT input_cooling_type FROM designs WHERE input_cooling_type IS NOT NULL"
            )
            cooling_types = [row[0] for row in cursor.fetchall()]

            # Malzemeler
            cursor.execute(
                "SELECT DISTINCT input_hv_material FROM designs WHERE input_hv_material IS NOT NULL"
            )
            hv_materials = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                "SELECT DISTINCT input_lv_material FROM designs WHERE input_lv_material IS NOT NULL"
            )
            lv_materials = [row[0] for row in cursor.fetchall()]

            return {
                "total_designs": total,
                "rating_range": {
                    "min": rating_range[0],
                    "max": rating_range[1]
                },
                "high_voltage_range": {
                    "min": hv_range[0],
                    "max": hv_range[1]
                },
                "vector_groups": vector_groups,
                "cooling_types": cooling_types,
                "materials": {
                    "hv": hv_materials,
                    "lv": lv_materials
                }
            }

    def bulk_insert(self, designs: List[TransformerSpecs]) -> int:
        """Toplu ekleme (ilk yükleme için)"""
        count = 0
        for specs in designs:
            try:
                self.upsert_design(specs)
                count += 1
            except Exception as e:
                print(f"Hata: {specs.design_number} - {e}")
        return count


# Singleton instance
_db_service: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    """DatabaseService singleton döndür"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
