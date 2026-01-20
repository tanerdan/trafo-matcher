"""SQLite veritabanı bağlantı ve tablo yönetimi"""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
import os

# Veritabanı dosyası yolu
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "trafo_designs.db"


def get_db_path() -> Path:
    """Veritabanı dosya yolunu döndür"""
    db_path = os.getenv("DATABASE_PATH")
    if db_path:
        return Path(db_path)
    return DEFAULT_DB_PATH


@contextmanager
def get_connection():
    """Veritabanı bağlantısı context manager"""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Dict-like erişim için
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Veritabanı tablolarını oluştur"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Designs tablosu - 56 alan + meta bilgiler
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS designs (
                -- META BİLGİLER
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                design_number TEXT UNIQUE NOT NULL,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- INPUT SPECIFICATIONS SHEET (24 alan)
                -- Güç ve Gerilim
                input_rating_kva REAL,
                input_onaf_rating_kva REAL,
                input_high_voltage_v REAL,
                input_low_voltage_v REAL,

                -- Bağlantı
                input_connection_hv TEXT,
                input_connection_lv TEXT,

                -- Elektriksel
                input_frequency_hz REAL,
                input_no_load_loss_w REAL,
                input_load_loss_w REAL,
                input_impedance_percent REAL,
                input_no_load_current_percent REAL,
                input_clock_number INTEGER,

                -- Soğutma ve Malzeme
                input_cooling_type TEXT,
                input_lv_material TEXT,
                input_hv_material TEXT,
                input_lv_winding_type TEXT,
                input_hv_wire_type TEXT,
                input_lv_wire_type TEXT,
                input_core_shape TEXT,

                -- Sıcaklık
                input_ambient_temp_c REAL,
                input_top_oil_rise_k REAL,
                input_winding_rise_k REAL,
                input_hotspot_k REAL,

                -- OUTPUT SHEET (32 alan)
                -- Bağlantı
                output_vector_group TEXT,
                output_voltage_lv_v REAL,
                output_voltage_hv_v REAL,

                -- Nüve
                output_core_diameter_mm REAL,
                output_core_section_cm2 REAL,
                output_core_weight_kg REAL,
                output_core_material TEXT,
                output_induction_tesla REAL,

                -- Hesaplanan Kayıplar
                output_no_load_loss_w REAL,
                output_no_load_current_percent REAL,
                output_load_loss_w REAL,
                output_impedance_percent REAL,

                -- Verimlilik
                output_pei REAL,
                output_efficiency_percent REAL,
                output_sound_power_db REAL,

                -- Sıcaklık (Hesaplanan)
                output_top_oil_rise_k REAL,
                output_winding_temp_hv_k REAL,
                output_winding_temp_lv_k REAL,
                output_hotspot_k REAL,

                -- Ağırlıklar
                output_weight_lv_kg REAL,
                output_weight_hv_kg REAL,
                output_total_weight_kg REAL,
                output_oil_volume_l REAL,

                -- Tank Boyutları
                output_tank_length_mm REAL,
                output_tank_width_mm REAL,
                output_tank_height_mm REAL,

                -- AG Sargı Detayları
                output_foil_height_mm REAL,
                output_foil_thickness_mm REAL,
                output_turns_lv INTEGER,
                output_turns_hv INTEGER,

                -- Sargı Çapları
                output_inner_diameter_lv_mm REAL,
                output_outer_diameter_lv_mm REAL,
                output_inner_diameter_hv_mm REAL,
                output_outer_diameter_hv_mm REAL,

                -- Akımlar
                output_phase_current_lv_a REAL,
                output_phase_current_hv_a REAL,
                output_current_density_lv REAL,
                output_current_density_hv REAL,

                -- Diğer
                output_volts_per_turn REAL,
                output_cost_dollar REAL
            )
        """)

        # Hızlı arama için index'ler
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rating
            ON designs(input_rating_kva)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_voltages
            ON designs(input_high_voltage_v, input_low_voltage_v)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vector_group
            ON designs(output_vector_group)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cooling
            ON designs(input_cooling_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_materials
            ON designs(input_hv_material, input_lv_material)
        """)

        conn.commit()
        print("Veritabanı tabloları oluşturuldu.")


def drop_all_tables():
    """Tüm tabloları sil (dikkatli kullanın!)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS designs")
        conn.commit()
        print("Tüm tablolar silindi.")


def get_table_info():
    """Tablo bilgilerini döndür"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(designs)")
        columns = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM designs")
        count = cursor.fetchone()[0]

        return {
            "columns": [dict(col) for col in columns],
            "row_count": count
        }


if __name__ == "__main__":
    # Test
    init_database()
    info = get_table_info()
    print(f"Tablo sütun sayısı: {len(info['columns'])}")
    print(f"Kayıt sayısı: {info['row_count']}")
