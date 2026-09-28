from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import router
from backend.app.config import get_settings
from backend.app.database import Base, engine


settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MedAnnotate AI API",
    version="1.0.0",
    description=(
        "Full-stack medical-image annotation and dataset-management research prototype."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "MedAnnotate AI API",
        "docs": "/docs",
        "research_use_only": True,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database": settings.database_url.split(":", 1)[0],
        "model_checkpoint_configured": bool(settings.model_path),
        "demo_mode_allowed": settings.allow_demo_mode,
    }
