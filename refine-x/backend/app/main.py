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
    return {"status": "healthy"}


app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(cleaning_router)
app.include_router(ai_analysis_router)
app.include_router(charts_router)
app.include_router(insights_router)
app.include_router(comparison_router)
