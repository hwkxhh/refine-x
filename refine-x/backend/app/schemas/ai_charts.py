from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel


# ── Phase 3 AI header analysis ───────────────────────────────────────────────

class UnnecessaryColumn(BaseModel):
    column: str
    reason: str
    impact_if_removed: str


class HeaderAnalysisResponse(BaseModel):
    job_id: int
    unnecessary_columns: list[UnnecessaryColumn]
    essential_columns: list[str]
    dataset_summary: str


class DropColumnsRequest(BaseModel):
    columns: list[str]


class SuggestedAnalysis(BaseModel):
    name: str
    description: str
    columns_needed: list[str]
    formula_type: str
    example: str


class RecommendedViz(BaseModel):
    chart_type: str
    x_column: str
    y_column: str
    reason: str


class FormulaSuggestionsResponse(BaseModel):
    job_id: int
    suggested_analyses: list[SuggestedAnalysis]
    recommended_visualizations: list[RecommendedViz]


# ── Phase 4 charts ───────────────────────────────────────────────────────────

class GoalRequest(BaseModel):
    goal_text: str
    goal_category: str = "custom"


class GoalResponse(BaseModel):
    id: int
    job_id: int
    goal_text: str
    goal_category: str

    model_config = {"from_attributes": True}


class RecommendationItem(BaseModel):
    x_col: str
    y_col: Optional[str]
    chart_type: str
    relevance_score: float
    reasoning: str


class GenerateChartRequest(BaseModel):
    x_col: str
    y_col: Optional[str] = None
    is_recommended: bool = False


class ChartResponse(BaseModel):
    id: int
    job_id: int
    chart_type: str
    x_header: str
    y_header: Optional[str]
    title: str
    data: Any
    config: Optional[Any]
    is_recommended: bool

    model_config = {"from_attributes": True}


class ChartListItem(BaseModel):
    id: int
    job_id: int
    chart_type: str
    x_header: str
    y_header: Optional[str]
    title: str
    is_recommended: bool

    model_config = {"from_attributes": True}


# ── Phase 5 insights + annotations ──────────────────────────────────────────

class InsightResponse(BaseModel):
    id: int
    chart_id: Optional[int]
    job_id: int
    content: str
    confidence: str
    confidence_score: float
    recommendations: Optional[Any]

    model_config = {"from_attributes": True}


class AnnotationRequest(BaseModel):
    data_point_index: int
    text: str


class AnnotationResponse(BaseModel):
    id: int
    chart_id: int
    user_id: int
    data_point_index: int
    text: str

    model_config = {"from_attributes": True}


# ── Phase 6 comparison ───────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    job_id_1: int
    job_id_2: int


class ConfirmMappingRequest(BaseModel):
    mapping: dict[str, str]   # {df1_col: df2_col}


class ComparisonResponse(BaseModel):
    id: int
    status: str
    header_mapping: Optional[Any]
    deltas: Optional[Any]
    significant_changes: Optional[Any]
    ai_insight: Optional[str]

    model_config = {"from_attributes": True}
