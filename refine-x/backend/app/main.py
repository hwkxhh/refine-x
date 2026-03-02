from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.upload import router as upload_router
from app.routes.cleaning import router as cleaning_router
from app.routes.ai_analysis import router as ai_analysis_router
from app.routes.charts import router as charts_router
from app.routes.insights import router as insights_router
from app.routes.comparison import router as comparison_router

app = FastAPI(title="RefineX API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "RefineX API is running", "version": "1.0.0"}


@app.get("/health")
def health():
    from app.config import settings
    results = {}
    overall = "healthy"

    # ── PostgreSQL ────────────────────────────────────────────────────
    try:
        from app.database import engine
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        results["database"] = "healthy"
    except Exception as e:
        results["database"] = f"unhealthy: {e}"
        overall = "degraded"

    # ── Redis ─────────────────────────────────────────────────────────
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        r.ping()
        results["redis"] = "healthy"
    except Exception as e:
        results["redis"] = f"unhealthy: {e}"
        overall = "degraded"

    # ── Celery ────────────────────────────────────────────────────────
    try:
        from celery_app import celery_app
        insp = celery_app.control.inspect(timeout=3)
        active = insp.ping()
        if active:
            results["celery"] = "healthy"
        else:
            results["celery"] = "unhealthy: no workers responding"
            overall = "degraded"
    except Exception as e:
        results["celery"] = f"unhealthy: {e}"
        overall = "degraded"

    # ── MinIO ─────────────────────────────────────────────────────────
    try:
        from app.services.storage import storage_service
        storage_service.s3_client.list_buckets()
        results["minio"] = "healthy"
    except Exception as e:
        results["minio"] = f"unhealthy: {e}"
        overall = "degraded"

    return {"status": overall, "services": results}


app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(cleaning_router)
app.include_router(ai_analysis_router)
app.include_router(charts_router)
app.include_router(insights_router)
app.include_router(comparison_router)
