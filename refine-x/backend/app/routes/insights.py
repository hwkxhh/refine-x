from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.annotation import Annotation
from app.models.chart import Chart
from app.models.insight import Insight
from app.models.upload_job import UploadJob
from app.models.user import User
from app.models.user_goal import UserGoal
from app.schemas.ai_charts import (
    AnnotationRequest,
    AnnotationResponse,
    InsightResponse,
)
from app.services.ai_insights import generate_chart_insight
from app.services.auth import get_current_user
from app.services.cache import get_cached_dataframe

router = APIRouter(tags=["insights-annotations"])


def _get_chart_or_404(chart_id: int, user: User, db: Session) -> Chart:
    chart = db.query(Chart).filter(Chart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    # Verify ownership via job
    job = db.query(UploadJob).filter(UploadJob.id == chart.job_id).first()
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Chart not found")
    return chart


# ── Insights ──────────────────────────────────────────────────────────────────

@router.post("/charts/{chart_id}/insights", response_model=InsightResponse, status_code=201)
def generate_insight(
    chart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chart = _get_chart_or_404(chart_id, current_user, db)
    goal = db.query(UserGoal).filter(UserGoal.job_id == chart.job_id).first()
    user_goal = goal.goal_text if goal else "General data analysis"

    df = get_cached_dataframe(chart.job_id)
    if df is None:
        raise HTTPException(status_code=422, detail="Cached data not available")

    result = generate_chart_insight(
        chart_type=chart.chart_type,
        x_header=chart.x_header,
        y_header=chart.y_header,
        chart_data=chart.data or [],
        user_goal=user_goal,
    )

    insight = Insight(
        chart_id=chart_id,
        job_id=chart.job_id,
        content=result["insight"],
        confidence=result["confidence"],
        confidence_score=result["confidence_score"],
        recommendations=result.get("recommendations", []),
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


@router.get("/jobs/{job_id}/insights", response_model=list[InsightResponse])
def list_insights(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return db.query(Insight).filter(Insight.job_id == job_id).order_by(Insight.created_at.desc()).all()


@router.get("/insights/{insight_id}", response_model=InsightResponse)
def get_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    job = db.query(UploadJob).filter(UploadJob.id == insight.job_id).first()
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight


# ── Annotations ───────────────────────────────────────────────────────────────

@router.post("/charts/{chart_id}/annotations", response_model=AnnotationResponse, status_code=201)
def add_annotation(
    chart_id: int,
    payload: AnnotationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_chart_or_404(chart_id, current_user, db)
    ann = Annotation(
        chart_id=chart_id,
        user_id=current_user.id,
        data_point_index=payload.data_point_index,
        text=payload.text,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return ann


@router.get("/charts/{chart_id}/annotations", response_model=list[AnnotationResponse])
def list_annotations(
    chart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chart = db.query(Chart).filter(Chart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    return db.query(Annotation).filter(Annotation.chart_id == chart_id).order_by(Annotation.created_at).all()


@router.delete("/annotations/{annotation_id}")
def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ann = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Annotation not found")
    if ann.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's annotation")
    db.delete(ann)
    db.commit()
    return {"message": "Annotation deleted"}
