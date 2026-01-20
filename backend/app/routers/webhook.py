"""N8N Webhook endpoint'leri

Bu modül n8n workflow'larından gelen istekleri işler:
- Yeni dizayn dosyası bildirimi
- Dizayn güncelleme bildirimi
- Dizayn silme bildirimi
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os

from ..services.excel_parser import ExcelParser
from ..services.db_service import get_db_service, DatabaseService

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


class NewDesignRequest(BaseModel):
    """Yeni dizayn bildirimi"""
    file_path: str
    action: Optional[str] = "add"  # add, update, delete


class WebhookResponse(BaseModel):
    """Webhook yanıtı"""
    success: bool
    message: str
    design_number: Optional[str] = None
    details: Optional[dict] = None


def get_excel_parser() -> ExcelParser:
    """Excel parser instance döndür"""
    designs_dir = os.getenv("DESIGNS_DIRECTORY", "Z:\\")
    return ExcelParser(designs_dir)


@router.post("/new-design", response_model=WebhookResponse)
async def handle_new_design(
    request: NewDesignRequest,
    background_tasks: BackgroundTasks,
    db_service: DatabaseService = Depends(get_db_service),
    excel_parser: ExcelParser = Depends(get_excel_parser)
):
    """
    N8N'den yeni dizayn bildirimi al ve veritabanına ekle.

    N8N Workflow Örneği:
    1. File Watcher: Z:\\ dizininde yeni .xlsx dosyası algıla
    2. HTTP Request: POST /api/webhook/new-design
       Body: {"file_path": "Z:\\yeni_dizayn.xlsx", "action": "add"}

    Actions:
    - add: Yeni dizayn ekle (varsayılan)
    - update: Mevcut dizaynı güncelle
    - delete: Dizaynı sil
    """
    file_path = Path(request.file_path)

    # Dosya varlık kontrolü
    if request.action != "delete" and not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dosya bulunamadı: {request.file_path}"
        )

    # Dosya uzantısı kontrolü
    if request.action != "delete" and file_path.suffix.lower() not in [".xlsx", ".xlsm"]:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz dosya türü: {file_path.suffix}. Sadece .xlsx ve .xlsm desteklenir."
        )

    design_number = file_path.stem

    try:
        if request.action == "delete":
            # Dizaynı sil
            design = db_service.get_design_by_number(design_number)
            if design:
                db_service.delete_design(design.id)
                return WebhookResponse(
                    success=True,
                    message=f"Dizayn silindi: {design_number}",
                    design_number=design_number
                )
            else:
                return WebhookResponse(
                    success=False,
                    message=f"Dizayn bulunamadı: {design_number}",
                    design_number=design_number
                )

        # Excel dosyasını parse et
        specs = excel_parser.parse_single_file(str(file_path))

        if not specs:
            return WebhookResponse(
                success=False,
                message=f"Dosya parse edilemedi: {design_number}. 'Input specifications' ve 'Output' sheet'leri gerekli.",
                design_number=design_number
            )

        if not specs.input_rating_kva:
            return WebhookResponse(
                success=False,
                message=f"Dosyada Rating değeri bulunamadı: {design_number}",
                design_number=design_number
            )

        # Veritabanına ekle/güncelle
        design_id = db_service.upsert_design(specs)

        action_text = "güncellendi" if request.action == "update" else "eklendi"

        return WebhookResponse(
            success=True,
            message=f"Dizayn {action_text}: {design_number}",
            design_number=design_number,
            details={
                "id": design_id,
                "rating_kva": specs.input_rating_kva,
                "high_voltage_v": specs.input_high_voltage_v,
                "low_voltage_v": specs.input_low_voltage_v,
                "vector_group": specs.output_vector_group
            }
        )

    except Exception as e:
        return WebhookResponse(
            success=False,
            message=f"Hata: {str(e)}",
            design_number=design_number
        )


@router.post("/bulk-sync")
async def bulk_sync(
    db_service: DatabaseService = Depends(get_db_service),
    excel_parser: ExcelParser = Depends(get_excel_parser)
):
    """
    Tüm Excel dosyalarını yeniden tara ve veritabanını senkronize et.

    Bu endpoint:
    1. Z:\\ dizinindeki tüm geçerli Excel dosyalarını bulur
    2. Her dosyayı parse eder
    3. Veritabanına ekler veya günceller
    """
    try:
        # Geçerli dosyaları bul
        valid_files = excel_parser.find_valid_design_files()

        success_count = 0
        error_count = 0
        errors = []

        for file_path in valid_files:
            try:
                specs = excel_parser.parse_excel_file(file_path)
                if specs and specs.input_rating_kva:
                    db_service.upsert_design(specs)
                    success_count += 1
                else:
                    errors.append(f"{file_path.name}: Rating bulunamadı")
                    error_count += 1
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
                error_count += 1

        return {
            "success": True,
            "message": f"Senkronizasyon tamamlandı",
            "details": {
                "total_files": len(valid_files),
                "success": success_count,
                "errors": error_count,
                "error_list": errors[:10] if errors else []
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Senkronizasyon hatası: {str(e)}"
        )


@router.get("/status")
async def webhook_status(
    db_service: DatabaseService = Depends(get_db_service)
):
    """Webhook durumu ve veritabanı istatistikleri"""
    stats = db_service.get_stats()
    designs_dir = os.getenv("DESIGNS_DIRECTORY", "Z:\\")

    return {
        "status": "active",
        "designs_directory": designs_dir,
        "database_stats": stats,
        "endpoints": {
            "new_design": "POST /api/webhook/new-design",
            "bulk_sync": "POST /api/webhook/bulk-sync",
            "status": "GET /api/webhook/status"
        }
    }
