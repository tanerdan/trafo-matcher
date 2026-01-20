from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routers import search, webhook
from .services.database import init_database
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

app = FastAPI(
    title="Trafo Matcher",
    description="Trafo dizayn eşleştirme API'si - Doğal dil sorguları ve form tabanlı arama ile en uygun trafo dizaynlarını bulun",
    version="2.0.0"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da kısıtlanmalı
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(search.router)
app.include_router(webhook.router)


@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında veritabanını hazırla"""
    init_database()


@app.get("/")
async def root():
    return {
        "message": "Trafo Matcher API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "search": "POST /api/search - Doğal dil ile trafo ara (LLM)",
            "search_form": "POST /api/search/form - Form ile trafo ara (hızlı)",
            "designs": "GET /api/designs - Tüm dizaynları listele",
            "stats": "GET /api/stats - Veritabanı istatistikleri",
            "health": "GET /api/health - Sistem durumu",
            "webhook": "POST /api/webhook/new-design - N8N webhook"
        }
    }


# Frontend static dosyaları (build sonrası)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
