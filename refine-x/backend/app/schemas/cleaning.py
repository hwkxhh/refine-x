from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CleaningSummaryResponse(BaseModel):
    job_id: int
    row_count_original: Optional[int]
    row_count_cleaned: Optional[int]
    duplicates_removed: int
    columns_renamed: int
    columns_dropped: int
    dates_converted: int
    ages_bucketed: int
    missing_filled: int
    outliers_flagged: int
    quality_score: Optional[float]
    column_metadata: Optional[dict[str, Any]]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AuditLogEntry(BaseModel):
    id: int
    job_id: int
    row_index: Optional[int]
    column_name: Optional[str]
    action: str
    original_value: Optional[str]
    new_value: Optional[str]
    reason: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class MissingFieldsResponse(BaseModel):
    job_id: int
    missing: dict[str, dict]   # {col: {count, percentage}}


class ManualFillRequest(BaseModel):
    column: str
    row_indices: list[int]
    values: list[str]


class OutlierEntry(BaseModel):
    row_index: int
    column: str
    value: Any
    expected_range: str


class OutliersResponse(BaseModel):
    job_id: int
    outliers: list[OutlierEntry]


class ResolveOutlierRequest(BaseModel):
    row_index: int
    action: str   # 'keep' | 'remove'
