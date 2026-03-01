from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.comparison_job import ComparisonJob
from app.models.upload_job import UploadJob
from app.models.user import User
from app.schemas.ai_charts import (
    CompareRequest,
    ComparisonResponse,
    ConfirmMappingRequest,
)
from app.services.ai_insights import generate_comparison_insight
from app.services.auth import get_current_user
from app.services.cache import get_cached_dataframe
from app.services.comparison import DatasetComparison

router = APIRouter(prefix="/compare", tags=["comparison"])


def _get_comp_or_404(comp_id: int, user: User, db: Session) -> ComparisonJob:
    comp = db.query(ComparisonJob).filter(ComparisonJob.id == comp_id).first()
    if not comp or comp.user_id != user.id:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return comp


# ── Create comparison ─────────────────────────────────────────────────────────

@router.post("", response_model=ComparisonResponse, status_code=201)
def create_comparison(
    payload: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for jid in (payload.job_id_1, payload.job_id_2):
        job = db.query(UploadJob).filter(UploadJob.id == jid).first()
        if not job or job.user_id != current_user.id:
            raise HTTPException(status_code=404, detail=f"Job {jid} not found")

    df1 = get_cached_dataframe(payload.job_id_1)
    df2 = get_cached_dataframe(payload.job_id_2)
    if df1 is None or df2 is None:
        raise HTTPException(status_code=422, detail="One or both datasets not in cache")

    comp_svc = DatasetComparison(df1, df2)
    raw_mapping = comp_svc.fuzzy_match_headers()
    # Flatten to {df1_col: df2_col} for storage
    flat_mapping = {k: v["df2_col"] for k, v in raw_mapping.items()}
    similarity_info = {k: v["similarity"] for k, v in raw_mapping.items()}

    comp = ComparisonJob(
        user_id=current_user.id,
        job_id_1=payload.job_id_1,
        job_id_2=payload.job_id_2,
        header_mapping={"mapping": flat_mapping, "similarity": similarity_info},
        status="pending",
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


# ── Confirm mapping + compute deltas ─────────────────────────────────────────

@router.post("/{comparison_id}/confirm-mapping")
def confirm_mapping(
    comparison_id: int,
    payload: ConfirmMappingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comp = _get_comp_or_404(comparison_id, current_user, db)

    df1 = get_cached_dataframe(comp.job_id_1)
    df2 = get_cached_dataframe(comp.job_id_2)
    if df1 is None or df2 is None:
        raise HTTPException(status_code=422, detail="One or both datasets not in cache")

    svc = DatasetComparison(df1, df2)
    aligned1, aligned2 = svc.align_datasets(payload.mapping)
    deltas = svc.calculate_deltas(aligned1, aligned2)
    significant = svc.flag_significant_changes(deltas)

    from sqlalchemy.orm.attributes import flag_modified
    comp.header_mapping = {"mapping": payload.mapping}
    comp.deltas = deltas
    comp.significant_changes = significant
    comp.status = "completed"
    flag_modified(comp, "header_mapping")
    flag_modified(comp, "deltas")
    flag_modified(comp, "significant_changes")
    db.commit()

    return {"message": "Mapping confirmed and deltas calculated", "comparison_id": comparison_id}


# ── Results ───────────────────────────────────────────────────────────────────

@router.get("/{comparison_id}/deltas")
def get_deltas(
    comparison_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comp = _get_comp_or_404(comparison_id, current_user, db)
    if comp.status != "completed":
        raise HTTPException(status_code=400, detail="Confirm mapping first")
    return {"comparison_id": comparison_id, "deltas": comp.deltas}


@router.get("/{comparison_id}/significant-changes")
def get_significant_changes(
    comparison_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comp = _get_comp_or_404(comparison_id, current_user, db)
    if comp.status != "completed":
        raise HTTPException(status_code=400, detail="Confirm mapping first")
    return {"comparison_id": comparison_id, "significant_changes": comp.significant_changes}


@router.post("/{comparison_id}/insights")
def get_comparison_insight(
    comparison_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comp = _get_comp_or_404(comparison_id, current_user, db)
    if comp.status != "completed":
        raise HTTPException(status_code=400, detail="Confirm mapping first")

    insight = generate_comparison_insight(
        deltas=comp.deltas or [],
        significant=comp.significant_changes or [],
    )
    comp.ai_insight = insight
    db.commit()
    return {"comparison_id": comparison_id, "insight": insight}
