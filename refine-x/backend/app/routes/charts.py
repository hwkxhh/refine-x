from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from openai import RateLimitError, AuthenticationError, APIStatusError
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
from app.services.chart_suite import generate_full_chart_suite
from app.services.column_role_classifier import get_plottable_columns, NEVER_USE_AS_AXIS

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

    # Only expose plottable columns to the recommendation engine
    _role_info = get_plottable_columns(df)
    _blocked_rec = {b["column"] for b in _role_info["blocked"]}
    safe_column_names = [c for c in df.columns.tolist() if c not in _blocked_rec]

    try:
        recs = recommend_headers(
            column_names=safe_column_names,
            data_sample=sample,
            user_goal=goal.goal_text,
            df=df,
        )
    except (RateLimitError, AuthenticationError, APIStatusError):
        # GPT quota exhausted — return empty list gracefully
        recs = []
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

    # ── Role-gate: permanently block identifier/sequence/constant columns ───
    _role_info = get_plottable_columns(df)
    _blocked = {b["column"]: b["role"] for b in _role_info["blocked"]}
    if payload.x_col in _blocked:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Column '{payload.x_col}' cannot be used as a chart axis: "
                f"classified as '{_blocked[payload.x_col]}' "
                f"(identifiers, sequences, and constants are never plotted)."
            ),
        )
    if payload.y_col and payload.y_col in _blocked:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Column '{payload.y_col}' cannot be used as a chart axis: "
                f"classified as '{_blocked[payload.y_col]}' "
                f"(identifiers, sequences, and constants are never plotted)."
            ),
        )
    # Y axis must be a quantitative metric — not a category, date, or code
    if payload.y_col and payload.y_col not in _role_info["metric_cols"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Column '{payload.y_col}' is not a quantitative metric and "
                f"cannot be used as a Y axis. Only METRIC columns can be Y axes."
            ),
        )

    # Prevent nonsense same-column charts (e.g. "Year vs Year")
    y_col = None if payload.y_col == payload.x_col else payload.y_col

    # Validate group_by column exists
    group_by = payload.group_by if (payload.group_by and payload.group_by in df.columns) else None

    engine = ChartEngine(df)
    chart_type = engine.determine_chart_type(payload.x_col, y_col, group_by=group_by)
    chart_payload = engine.generate_chart_data(payload.x_col, y_col, chart_type, group_by=group_by)

    config = {
        "xLabel": chart_payload["xLabel"],
        "yLabel": chart_payload["yLabel"],
        "xDomain": chart_payload.get("xDomain"),
        "yDomain": chart_payload.get("yDomain"),
        "grouped": chart_payload.get("grouped", False),
        "series_keys": chart_payload.get("series_keys"),
        "group_by": group_by,
        "note": chart_payload.get("note"),
        "layout": chart_payload.get("layout"),
        "data_key": chart_payload.get("data_key", "y"),
        "x_data_key": chart_payload.get("x_data_key", "x"),
        "y_unit": chart_payload.get("y_unit", "plain"),
    }

    chart = Chart(
        job_id=job_id,
        chart_type=chart_type,
        x_header=payload.x_col,
        y_header=y_col,
        title=chart_payload["title"],
        data=chart_payload["data"],
        config=config,
        reason=payload.reason,
        is_recommended=payload.is_recommended,
    )
    db.add(chart)
    db.commit()
    db.refresh(chart)
    return chart


# ── Auto-generate full chart suite ────────────────────────────────────────────

@router.post("/{job_id}/charts/auto", response_model=list[ChartResponse], status_code=201)
def auto_generate_charts(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Automatically generate a full analyst-grade chart suite for the dataset.
    Produces 10-15 charts based on mandatory rules, deduplicating against
    any charts that already exist for this job.
    """
    _get_job_or_404(job_id, current_user, db)
    df = _get_df_or_422(job_id)

    # Gather existing charts to avoid duplicates
    existing = db.query(Chart).filter(Chart.job_id == job_id).all()
    existing_specs = [
        {"x_col": c.x_header, "y_col": c.y_header, "chart_type": c.chart_type}
        for c in existing
    ]

    # Load htype map if available
    from app.models.cleaned_dataset import CleanedDataset
    cd = db.query(CleanedDataset).filter(CleanedDataset.job_id == job_id).first()
    htypes = cd.htype_map if cd and cd.htype_map else {}
    derived_columns = cd.derived_metrics_info if cd and cd.derived_metrics_info else []

    # Load goal
    goal_row = db.query(UserGoal).filter(UserGoal.job_id == job_id).first()
    goal_text = goal_row.goal_text if goal_row else ""

    suite = generate_full_chart_suite(
        df=df,
        htypes=htypes,
        goal=goal_text,
        existing_charts=existing_specs,
        derived_columns=derived_columns,
    )

    engine = ChartEngine(df)
    created_charts = []

    for spec in suite:
        try:
            x_col = spec["x_col"]
            y_col = spec.get("y_col")
            chart_type = spec["chart_type"]
            group_by = spec.get("group_by")
            reason = spec.get("reason", "")

            chart_payload = engine.generate_chart_data(x_col, y_col, chart_type, group_by=group_by)

            config = {
                "xLabel": chart_payload["xLabel"],
                "yLabel": chart_payload["yLabel"],
                "xDomain": chart_payload.get("xDomain"),
                "yDomain": chart_payload.get("yDomain"),
                "grouped": chart_payload.get("grouped", False),
                "series_keys": chart_payload.get("series_keys"),
                "group_by": group_by,
                "note": chart_payload.get("note"),
                "layout": chart_payload.get("layout"),
                "data_key": chart_payload.get("data_key", "y"),
                "x_data_key": chart_payload.get("x_data_key", "x"),
                "y_unit": chart_payload.get("y_unit", "plain"),
            }

            chart = Chart(
                job_id=job_id,
                chart_type=chart_type,
                x_header=x_col,
                y_header=y_col,
                title=spec.get("title") or chart_payload["title"],
                data=chart_payload["data"],
                config=config,
                reason=reason,
                is_recommended=True,
            )
            db.add(chart)
            created_charts.append(chart)
        except Exception:
            # Skip charts that fail to generate (bad column combos etc)
            continue

    db.commit()
    for c in created_charts:
        db.refresh(c)

    return created_charts


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
