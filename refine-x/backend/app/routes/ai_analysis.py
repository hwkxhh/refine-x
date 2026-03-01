from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cleaning_log import CleaningLog
from app.models.upload_job import UploadJob
from app.models.user import User
from app.schemas.ai_charts import (
    DropColumnsRequest,
    FormulaSuggestionsResponse,
    HeaderAnalysisResponse,
)
from app.services.ai_analysis import analyze_headers, suggest_formulas
from app.services.auth import get_current_user
from app.services.cache import cache_dataframe, get_cached_dataframe
from datetime import datetime

router = APIRouter(prefix="/jobs", tags=["ai-analysis"])


def _get_job_or_404(job_id: int, user: User, db: Session) -> UploadJob:
    job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _get_df_or_422(job_id: int):
    df = get_cached_dataframe(job_id)
    if df is None:
        raise HTTPException(
            status_code=422,
            detail="Cleaned data not in cache. Re-upload or wait for processing.",
        )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: AI analyzes headers and flags unnecessary ones
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{job_id}/analyze-headers", response_model=HeaderAnalysisResponse)
def analyze_job_headers(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI reviews all column names + sample data and identifies:
    - Unnecessary columns (with reasons)
    - Essential columns
    - What the dataset is about
    """
    job = _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    sample_rows = df.head(5).fillna("").to_dict(orient="records")
    result = analyze_headers(
        columns=df.columns.tolist(),
        sample_rows=sample_rows,
        filename=job.filename,
    )

    return HeaderAnalysisResponse(
        job_id=job_id,
        unnecessary_columns=result.get("unnecessary_columns", []),
        essential_columns=result.get("essential_columns", []),
        dataset_summary=result.get("dataset_summary", ""),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: User confirms which columns to drop
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{job_id}/drop-columns")
def drop_columns(
    job_id: int,
    payload: DropColumnsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Drop the AI-suggested (or user-selected) columns from the cached DataFrame.
    Logs each removal to the audit trail.
    """
    _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    existing = [c for c in payload.columns if c in df.columns]
    missing = [c for c in payload.columns if c not in df.columns]

    for col in existing:
        log = CleaningLog(
            job_id=job_id,
            action="user_drop_column",
            reason="User confirmed AI recommendation to drop this column",
            column_name=col,
            timestamp=datetime.utcnow(),
        )
        db.add(log)

    df.drop(columns=existing, inplace=True)
    db.commit()
    cache_dataframe(job_id, df)

    return {
        "message": f"Dropped {len(existing)} column(s)",
        "dropped": existing,
        "not_found": missing,
        "remaining_columns": df.columns.tolist(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: AI suggests formulas and visualizations for the data
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{job_id}/formula-suggestions", response_model=FormulaSuggestionsResponse)
def formula_suggestions(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI suggests the most useful calculations, formulas, and chart pairings
    for the current (cleaned) dataset.
    """
    job = _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    # Use CleanedDataset summary if available
    from app.models.cleaned_dataset import CleanedDataset
    cleaned = db.query(CleanedDataset).filter(CleanedDataset.job_id == job_id).first()
    dataset_summary = None
    if cleaned and cleaned.cleaning_summary:
        dataset_summary = cleaned.cleaning_summary.get("dataset_summary")

    sample_rows = df.head(5).fillna("").to_dict(orient="records")
    result = suggest_formulas(
        columns=df.columns.tolist(),
        sample_rows=sample_rows,
        filename=job.filename,
        dataset_summary=dataset_summary,
    )

    return FormulaSuggestionsResponse(
        job_id=job_id,
        suggested_analyses=result.get("suggested_analyses", []),
        recommended_visualizations=result.get("recommended_visualizations", []),
    )
