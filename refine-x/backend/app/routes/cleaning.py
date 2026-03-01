from __future__ import annotations

import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cleaned_dataset import CleanedDataset
from app.models.cleaning_log import CleaningLog
from app.models.upload_job import UploadJob
from app.schemas.cleaning import (
    AuditLogEntry,
    CleaningSummaryResponse,
    ManualFillRequest,
    MissingFieldsResponse,
    OutliersResponse,
    ResolveOutlierRequest,
)
from app.services.auth import get_current_user
from app.services.cache import (
    cache_dataframe,
    delete_cached_dataframe,
    get_cached_dataframe,
)
from app.models.user import User

router = APIRouter(prefix="/jobs", tags=["cleaning"])


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
            detail="Cleaned data not in cache. Re-upload or wait for processing to complete.",
        )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Cleaning summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{job_id}/cleaning-summary", response_model=CleaningSummaryResponse)
def cleaning_summary(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    cleaned = db.query(CleanedDataset).filter(CleanedDataset.job_id == job_id).first()
    if not cleaned:
        raise HTTPException(status_code=404, detail="Cleaning results not available yet")

    summary = cleaned.cleaning_summary or {}
    return CleaningSummaryResponse(
        job_id=job_id,
        row_count_original=cleaned.row_count_original,
        row_count_cleaned=cleaned.row_count_cleaned,
        duplicates_removed=summary.get("duplicates_removed", 0),
        columns_renamed=summary.get("columns_renamed", 0),
        columns_dropped=summary.get("columns_dropped", 0),
        dates_converted=summary.get("dates_converted", 0),
        ages_bucketed=summary.get("ages_bucketed", 0),
        missing_filled=summary.get("missing_filled", 0),
        outliers_flagged=summary.get("outliers_flagged", 0),
        quality_score=cleaned.quality_score,
        column_metadata=cleaned.column_metadata,
        created_at=cleaned.created_at,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Audit trail
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{job_id}/audit-trail", response_model=list[AuditLogEntry])
def audit_trail(
    job_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    logs = (
        db.query(CleaningLog)
        .filter(CleaningLog.job_id == job_id)
        .order_by(CleaningLog.timestamp)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return logs


# ─────────────────────────────────────────────────────────────────────────────
# Missing fields
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{job_id}/missing-fields", response_model=MissingFieldsResponse)
def missing_fields(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    missing = {}
    for col in df.columns:
        count = int(df[col].isnull().sum())
        if count > 0:
            missing[col] = {"count": count, "percentage": round(count / len(df) * 100, 2)}

    return MissingFieldsResponse(job_id=job_id, missing=missing)


# ─────────────────────────────────────────────────────────────────────────────
# Manual fill
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{job_id}/fill-missing")
def fill_missing(
    job_id: int,
    payload: ManualFillRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    if payload.column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{payload.column}' not found")
    if len(payload.row_indices) != len(payload.values):
        raise HTTPException(status_code=400, detail="row_indices and values must be the same length")

    for idx, val in zip(payload.row_indices, payload.values):
        if idx < 0 or idx >= len(df):
            continue
        original = df.at[idx, payload.column]
        df.at[idx, payload.column] = val
        log = CleaningLog(
            job_id=job_id,
            action="fill_missing",
            reason="Manual fill by user",
            column_name=payload.column,
            row_index=idx,
            original_value=str(original) if original is not None else None,
            new_value=str(val),
        )
        db.add(log)

    db.commit()
    cache_dataframe(job_id, df)
    return {"message": f"Filled {len(payload.row_indices)} cell(s) in '{payload.column}'"}


# ─────────────────────────────────────────────────────────────────────────────
# Outliers
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{job_id}/outliers", response_model=OutliersResponse)
def get_outliers(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    logs = (
        db.query(CleaningLog)
        .filter(CleaningLog.job_id == job_id, CleaningLog.action == "flag_outlier")
        .all()
    )
    outliers = [
        {
            "row_index": log.row_index,
            "column": log.column_name,
            "value": log.original_value,
            "expected_range": log.reason.split("range ")[-1] if "range" in log.reason else "",
        }
        for log in logs
    ]
    return OutliersResponse(job_id=job_id, outliers=outliers)


@router.post("/{job_id}/resolve-outlier")
def resolve_outlier(
    job_id: int,
    payload: ResolveOutlierRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.action not in ("keep", "remove"):
        raise HTTPException(status_code=400, detail="action must be 'keep' or 'remove'")

    _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    if payload.action == "remove":
        if payload.row_index < 0 or payload.row_index >= len(df):
            raise HTTPException(status_code=400, detail="row_index out of range")
        df = df.drop(index=payload.row_index).reset_index(drop=True)
        log = CleaningLog(
            job_id=job_id,
            action="remove_outlier",
            reason=f"User chose to remove outlier at row {payload.row_index}",
            row_index=payload.row_index,
        )
        db.add(log)
        db.commit()
        cache_dataframe(job_id, df)
        return {"message": f"Row {payload.row_index} removed"}

    return {"message": f"Outlier at row {payload.row_index} kept"}


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{job_id}/export")
def export_csv(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    filename = f"cleaned_{job.filename}"
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
