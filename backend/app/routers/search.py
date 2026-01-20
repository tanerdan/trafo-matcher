from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..models.transformer import (
    TransformerQuery, SearchResponse, TransformerSpecs,
    TransformerMatch, FormSearchQuery
)
from ..services.db_service import get_db_service, DatabaseService
from ..services.similarity import SimilarityEngine
from ..services.ollama_service import OllamaService
import os

router = APIRouter(prefix="/api", tags=["search"])

# Global servis instances
_similarity_engine: Optional[SimilarityEngine] = None
_ollama_service: Optional[OllamaService] = None


def get_similarity_engine() -> SimilarityEngine:
    global _similarity_engine
    if _similarity_engine is None:
        _similarity_engine = SimilarityEngine()
    return _similarity_engine


def get_ollama_service() -> OllamaService:
    global _ollama_service
    if _ollama_service is None:
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        _ollama_service = OllamaService(base_url=ollama_url, model=ollama_model)
    return _ollama_service


@router.post("/search", response_model=SearchResponse)
async def search_transformers(
    query: TransformerQuery,
    db_service: DatabaseService = Depends(get_db_service),
    similarity_engine: SimilarityEngine = Depends(get_similarity_engine),
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """
    Doğal dil sorgusuyla trafo dizaynı ara (LLM kullanır).

    Örnek sorgular:
    - "100 kVA, 11000/415V Dyn11 trafo"
    - "250 kVA ONAN soğutmalı, bakır sargılı"
    - "Boşta kayıp 200W altında olan 160 kVA trafo"
    """
    # 1. Sorgudan parametreleri çıkar (LLM)
    raw_params = await ollama_service.extract_parameters(query.query)

    # Null ve None değerleri filtrele
    extracted_params = {
        k: v for k, v in raw_params.items()
        if v is not None and v != "" and v != "null"
    }

    if not extracted_params:
        raise HTTPException(
            status_code=400,
            detail="Sorgudan trafo parametresi çıkarılamadı. Lütfen güç (kVA), gerilim vb. belirtin."
        )

    # 2. Veritabanından tüm dizaynları al (çok hızlı)
    all_designs = db_service.get_all_designs()

    if not all_designs:
        raise HTTPException(
            status_code=404,
            detail="Veritabanında trafo bulunamadı. Lütfen init_database.py çalıştırın."
        )

    # 3. Benzer dizaynları bul
    matches = similarity_engine.find_similar_designs(
        query_specs=extracted_params,
        all_designs=all_designs,
        max_results=query.max_results
    )

    # 4. Basit açıklama
    explanation = f"{len(matches)} eşleşme bulundu."

    return SearchResponse(
        query=query.query,
        extracted_params=extracted_params,
        matches=matches,
        explanation=explanation
    )


@router.post("/search/form", response_model=SearchResponse)
async def search_transformers_form(
    query: FormSearchQuery,
    db_service: DatabaseService = Depends(get_db_service),
    similarity_engine: SimilarityEngine = Depends(get_similarity_engine)
):
    """
    Form tabanlı trafo arama (LLM kullanmaz, çok hızlı).

    Form alanları:
    - rating_kva: Güç (kVA)
    - high_voltage_v: YG Gerilim (V)
    - low_voltage_v: AG Gerilim (V)
    - vector_group: Vektör grubu (Dyn11, Yyn0, vb.)
    - cooling_type: Soğutma tipi (ONAN, ONAF, OFAF)
    - hv_material: YG malzemesi (cu, al)
    - lv_material: AG malzemesi (cu, al)
    - max_no_load_loss_w: Maksimum boşta kayıp (W)
    - max_load_loss_w: Maksimum yük kaybı (W)
    """
    # Form verilerini sorgu parametrelerine dönüştür
    extracted_params = {}

    if query.rating_kva is not None:
        extracted_params["rating_kva"] = query.rating_kva
    if query.high_voltage_v is not None:
        extracted_params["high_voltage_v"] = query.high_voltage_v
    if query.low_voltage_v is not None:
        extracted_params["low_voltage_v"] = query.low_voltage_v
    if query.vector_group is not None:
        extracted_params["vector_group"] = query.vector_group
    if query.cooling_type is not None:
        extracted_params["cooling_type"] = query.cooling_type
    if query.hv_material is not None:
        extracted_params["hv_material"] = query.hv_material
    if query.lv_material is not None:
        extracted_params["lv_material"] = query.lv_material
    if query.impedance_percent is not None:
        extracted_params["impedance_percent"] = query.impedance_percent
    if query.max_no_load_loss_w is not None:
        extracted_params["no_load_loss_w"] = query.max_no_load_loss_w
    if query.max_load_loss_w is not None:
        extracted_params["load_loss_w"] = query.max_load_loss_w

    if not extracted_params:
        raise HTTPException(
            status_code=400,
            detail="En az bir arama parametresi gerekli."
        )

    # Veritabanından tüm dizaynları al
    all_designs = db_service.get_all_designs()

    if not all_designs:
        raise HTTPException(
            status_code=404,
            detail="Veritabanında trafo bulunamadı. Lütfen init_database.py çalıştırın."
        )

    # Benzer dizaynları bul
    matches = similarity_engine.find_similar_designs(
        query_specs=extracted_params,
        all_designs=all_designs,
        max_results=query.max_results
    )

    # Sorgu özeti oluştur
    query_summary = ", ".join([f"{k}={v}" for k, v in extracted_params.items()])

    return SearchResponse(
        query=query_summary,
        extracted_params=extracted_params,
        matches=matches,
        explanation=f"{len(matches)} eşleşme bulundu."
    )


@router.get("/designs", response_model=List[TransformerSpecs])
async def list_designs(
    db_service: DatabaseService = Depends(get_db_service)
):
    """Tüm dizaynları listele"""
    return db_service.get_all_designs()


@router.get("/designs/{design_number}", response_model=TransformerSpecs)
async def get_design(
    design_number: str,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Belirli bir dizaynın detaylarını getir"""
    design = db_service.get_design_by_number(design_number)
    if not design:
        raise HTTPException(status_code=404, detail=f"Dizayn bulunamadı: {design_number}")
    return design


@router.get("/stats")
async def get_stats(
    db_service: DatabaseService = Depends(get_db_service)
):
    """Veritabanı istatistiklerini getir (form dropdown'ları için)"""
    return db_service.get_stats()


@router.get("/distinct/{field}")
async def get_distinct_values(
    field: str,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Bir alanın benzersiz değerlerini getir (dropdown için)"""
    allowed_fields = [
        "output_vector_group", "input_cooling_type",
        "input_hv_material", "input_lv_material",
        "output_core_material", "input_core_shape"
    ]
    if field not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"İzin verilen alanlar: {', '.join(allowed_fields)}"
        )
    return db_service.get_distinct_values(field)


@router.post("/refresh")
async def refresh_designs(
    db_service: DatabaseService = Depends(get_db_service)
):
    """Veritabanı istatistiklerini yenile (sayfa yenilemesi için)"""
    stats = db_service.get_stats()
    return {"message": f"{stats['total_designs']} dizayn mevcut", "stats": stats}


@router.get("/health")
async def health_check(
    db_service: DatabaseService = Depends(get_db_service),
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Sistem sağlık kontrolü"""
    ollama_connected = await ollama_service.check_connection()
    ollama_models = await ollama_service.get_available_models() if ollama_connected else []

    stats = db_service.get_stats()

    return {
        "status": "healthy",
        "database": {
            "connected": True,
            "designs_count": stats["total_designs"]
        },
        "ollama": {
            "connected": ollama_connected,
            "models": ollama_models
        }
    }
