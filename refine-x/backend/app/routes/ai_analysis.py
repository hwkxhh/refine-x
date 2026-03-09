from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cleaning_log import CleaningLog
from app.models.upload_job import UploadJob
from app.models.user import User
from app.schemas.ai_charts import (
    AnalyzedColumn,
    DropColumnsRequest,
    FormulaSuggestionsResponse,
    HeaderAnalysisResponse,
    UnnecessaryColumn,
)
from app.services.ai_analysis import suggest_formulas, suggest_analyses_and_viz
from app.services.column_relevance import analyze_columns_for_header_gate
from app.services.auth import get_current_user
from app.services.cache import cache_dataframe, get_cached_dataframe
from datetime import datetime

logger = logging.getLogger(__name__)
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
    GPT evaluates every column and explains:
    - What it actually measures (plain English)
    - Whether to keep or drop it (with specific reasoning)
    - What analysis it enables (for keep columns)
    - Any data quality warnings
    """
    job = _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    sample_rows = df.head(5).fillna("").to_dict(orient="records")
    columns = [str(c) for c in df.columns.tolist()]
    total_rows = len(df)

    # ── Call the new GPT-powered column analysis ──────────────────────────
    raw_results = analyze_columns_for_header_gate(
        columns=columns,
        sample_rows=sample_rows,
        filename=job.filename,
        total_rows=total_rows,
        df=df,
    )

    # ── Build typed response objects ──────────────────────────────────────
    analyzed: list[AnalyzedColumn] = []
    essential: list[str] = []
    unnecessary: list[UnnecessaryColumn] = []

    for item in raw_results:
        col = AnalyzedColumn(
            column=item["column"],
            decision=item["decision"],
            what_it_measures=item["what_it_measures"],
            why=item["why"],
            analytical_use=item.get("analytical_use"),
            warning=item.get("warning"),
        )
        analyzed.append(col)

        if item["decision"] == "keep":
            essential.append(item["column"])
        else:
            unnecessary.append(UnnecessaryColumn(
                column=item["column"],
                reason=item["why"],
                impact_if_removed="Low — this column was flagged as having minimal analytical value.",
            ))

    # ── Build dataset summary from GPT results ────────────────────────────
    keep_count = len(essential)
    drop_count = len(unnecessary)
    dataset_summary = (
        f"{job.filename} — {total_rows:,} rows × {len(columns)} columns. "
        f"AI recommends keeping {keep_count} column{'s' if keep_count != 1 else ''}"
        + (f" and dropping {drop_count}." if drop_count > 0 else ".")
    )

    return HeaderAnalysisResponse(
        job_id=job_id,
        columns=analyzed,
        essential_columns=essential,
        unnecessary_columns=unnecessary,
        dataset_summary=dataset_summary,
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
    columns = [str(c) for c in df.columns.tolist()]

    result = suggest_analyses_and_viz(
        columns=columns,
        sample_rows=sample_rows,
        filename=job.filename,
        df=df,
    )

    return FormulaSuggestionsResponse(
        job_id=job_id,
        suggested_analyses=result["suggested_analyses"],
        recommended_visualizations=result["recommended_visualizations"],
    )
