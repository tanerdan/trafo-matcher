#!/usr/bin/env python
r"""
Ilk veritabani yukleme scripti

Bu script:
1. SQLite veritabanini olusturur
2. Z:\ dizinindeki tum gecerli Excel dosyalarini tarar
3. Verileri veritabanina yazar

Kullanim:
    python scripts/init_database.py [--force]

Ortam degiskenleri:
    DESIGNS_DIRECTORY: Excel dizayn dosyalarinin bulundugu dizin (varsayilan: Z:\)
"""

import sys
import os
from pathlib import Path

# Backend modüllerini import edebilmek için path ekle
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.excel_parser import ExcelParser
from app.services.db_service import get_db_service, DatabaseService
from app.services.database import init_database, get_db_path


def main():
    # --force parametresi kontrolü
    force_mode = "--force" in sys.argv

    print("=" * 60)
    print("TRAFO MATCHER - VERITABANI BASLATMA")
    print("=" * 60)

    # Veritabanı yolu
    db_path = get_db_path()
    print(f"\nVeritabani yolu: {db_path}")

    # Dizayn dizini
    designs_dir = os.getenv("DESIGNS_DIRECTORY", "Z:\\")
    print(f"Dizayn dizini: {designs_dir}")

    # Dizin kontrolü
    if not Path(designs_dir).exists():
        print(f"\nHATA: Dizayn dizini bulunamadi: {designs_dir}")
        print("Lutfen Z: surucusunun bagli oldugundan emin olun veya")
        print("DESIGNS_DIRECTORY ortam degiskenini ayarlayin.")
        sys.exit(1)

    # Veritabanını başlat
    print("\n1. Veritabani tablolari olusturuluyor...")
    init_database()

    # Excel parser oluştur
    print("\n2. Excel dosyalari taraniyor...")
    parser = ExcelParser(designs_dir)

    # Geçerli dosyaları bul
    valid_files = parser.find_valid_design_files()
    print(f"   - Toplam gecerli dosya: {len(valid_files)}")

    if not valid_files:
        print("\nUYARI: Gecerli dizayn dosyasi bulunamadi!")
        print("'Input specifications' ve 'Output' sheet'leri olan .xlsx dosyalari araniyor.")
        sys.exit(1)

    # Veritabanı servisi
    db_service = get_db_service()

    # Mevcut kayıtları temizle (--force veya otomatik mod)
    existing_count = len(db_service.get_all_designs())
    if existing_count > 0:
        print(f"\n   - Mevcut kayit sayisi: {existing_count}")
        if force_mode:
            deleted = db_service.delete_all_designs()
            print(f"   - {deleted} kayit silindi (--force modu).")
        else:
            print("   - Mevcut kayitlar korunuyor, upsert yapilacak.")

    # Dosyaları parse et ve veritabanına ekle
    print("\n3. Dosyalar parse ediliyor ve veritabanina ekleniyor...")
    success_count = 0
    error_count = 0
    errors = []

    for i, file_path in enumerate(valid_files):
        try:
            # Progress göster
            if (i + 1) % 10 == 0 or i == len(valid_files) - 1:
                print(f"   Islenen: {i + 1}/{len(valid_files)}")

            # Parse et
            specs = parser.parse_excel_file(file_path)

            if specs and specs.input_rating_kva:
                # Veritabanına ekle (veya güncelle)
                db_service.upsert_design(specs)
                success_count += 1
            else:
                errors.append(f"{file_path.name}: Rating bulunamadi")
                error_count += 1

        except Exception as e:
            errors.append(f"{file_path.name}: {str(e)}")
            error_count += 1

    # Sonuç raporu
    print("\n" + "=" * 60)
    print("SONUC RAPORU")
    print("=" * 60)
    print(f"Basarili: {success_count}")
    print(f"Hatali: {error_count}")

    if errors:
        print(f"\nHatali dosyalar ({len(errors)}):")
        for err in errors[:10]:  # İlk 10 hata
            print(f"   - {err}")
        if len(errors) > 10:
            print(f"   ... ve {len(errors) - 10} hata daha")

    # İstatistikleri göster
    print("\nVERITABANI ISTATISTIKLERI:")
    stats = db_service.get_stats()
    print(f"   - Toplam dizayn: {stats['total_designs']}")
    if stats['rating_range']['min']:
        print(f"   - Guc araligi: {stats['rating_range']['min']} - {stats['rating_range']['max']} kVA")
    if stats['high_voltage_range']['min']:
        print(f"   - YG araligi: {stats['high_voltage_range']['min']} - {stats['high_voltage_range']['max']} V")
    if stats['vector_groups']:
        print(f"   - Vektor gruplari: {', '.join(str(v) for v in stats['vector_groups'] if v)}")
    if stats['cooling_types']:
        print(f"   - Sogutma tipleri: {', '.join(str(c) for c in stats['cooling_types'] if c)}")
    if stats['materials']['hv']:
        print(f"   - YG malzemeleri: {', '.join(str(m) for m in stats['materials']['hv'] if m)}")
    if stats['materials']['lv']:
        print(f"   - AG malzemeleri: {', '.join(str(m) for m in stats['materials']['lv'] if m)}")

    print("\n" + "=" * 60)
    print("Veritabani basariyla olusturuldu!")
    print(f"Dosya: {db_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
