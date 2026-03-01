from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chart import Chart
from app.models.upload_job import UploadJob
from app.models.user import User
from app.models.user_goal import UserGoal
from app.schemas.ai_charts import (
    ChartListItem,
    ChartResponse,
    GenerateChartRequest,
    GoalRequest,
    GoalResponse,
    RecommendationItem,
)
from app.services.ai_recommendations import recommend_headers
from app.services.auth import get_current_user
from app.services.cache import get_cached_dataframe
from app.services.chart_engine import ChartEngine

router = APIRouter(prefix="/jobs", tags=["charts"])


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


# ── Goal ─────────────────────────────────────────────────────────────────────

@router.post("/{job_id}/goal", response_model=GoalResponse)
def set_goal(
    job_id: int,
    payload: GoalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    goal = db.query(UserGoal).filter(UserGoal.job_id == job_id).first()
    if goal:
        goal.goal_text = payload.goal_text
        goal.goal_category = payload.goal_category
    else:
        goal = UserGoal(job_id=job_id, goal_text=payload.goal_text, goal_category=payload.goal_category)
        db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/{job_id}/goal", response_model=GoalResponse)
def get_goal(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    goal = db.query(UserGoal).filter(UserGoal.job_id == job_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="No goal set for this job")
    return goal


# ── AI Recommendations ────────────────────────────────────────────────────────

@router.get("/{job_id}/recommendations", response_model=list[RecommendationItem])
def get_recommendations(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    goal = db.query(UserGoal).filter(UserGoal.job_id == job_id).first()
    if not goal:
        raise HTTPException(status_code=400, detail="Set a goal first via POST /jobs/{job_id}/goal")

    df = _get_df_or_422(job_id)
    sample = df.head(5).fillna("").to_dict(orient="records")
    recs = recommend_headers(
        column_names=df.columns.tolist(),
        data_sample=sample,
        user_goal=goal.goal_text,
    )
    return recs


# ── Chart Generation ──────────────────────────────────────────────────────────

@router.post("/{job_id}/charts", response_model=ChartResponse, status_code=201)
def generate_chart(
    job_id: int,
    payload: GenerateChartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    if payload.x_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{payload.x_col}' not found in dataset")
    if payload.y_col and payload.y_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{payload.y_col}' not found in dataset")

    engine = ChartEngine(df)
    chart_type = engine.determine_chart_type(payload.x_col, payload.y_col)
    chart_payload = engine.generate_chart_data(payload.x_col, payload.y_col, chart_type)

    chart = Chart(
        job_id=job_id,
        chart_type=chart_type,
        x_header=payload.x_col,
        y_header=payload.y_col,
        title=chart_payload["title"],
        data=chart_payload["data"],
        config={"xLabel": chart_payload["xLabel"], "yLabel": chart_payload["yLabel"]},
        is_recommended=payload.is_recommended,
    )
    db.add(chart)
    db.commit()
    db.refresh(chart)
    return chart


# ── Chart List / Detail / Delete ─────────────────────────────────────────────

@router.get("/{job_id}/charts", response_model=list[ChartListItem])
def list_charts(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    return db.query(Chart).filter(Chart.job_id == job_id).order_by(Chart.created_at.desc()).all()


@router.get("/{job_id}/charts/{chart_id}", response_model=ChartResponse)
def get_chart(
    job_id: int,
    chart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    chart = db.query(Chart).filter(Chart.id == chart_id, Chart.job_id == job_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    return chart


@router.delete("/{job_id}/charts/{chart_id}")
def delete_chart(
    job_id: int,
    chart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    chart = db.query(Chart).filter(Chart.id == chart_id, Chart.job_id == job_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    db.delete(chart)
    db.commit()
    return {"message": "Chart deleted"}


# ── Correlation Heatmap ───────────────────────────────────────────────────────

@router.get("/{job_id}/correlation")
def correlation_heatmap(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)
    engine = ChartEngine(df)
    return engine.generate_correlation_heatmap()
