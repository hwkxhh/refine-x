from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, List, Optional


class UploadJobResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    file_type: str
    status: str
    quality_score: Optional[float] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    column_relevance_result: Optional[Dict[str, Any]] = None
    confirmed_columns: Optional[List[str]] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UploadJobListResponse(BaseModel):
    id: int
    filename: str
    status: str
    quality_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobStatusResponse(BaseModel):
    job_id: int
    status: str
    progress: Optional[int] = None
    quality_score: Optional[float] = None
    row_count: Optional[int] = None
    error_message: Optional[str] = None
    column_relevance_result: Optional[Dict[str, Any]] = None


class ColumnReviewRequest(BaseModel):
    """Body for POST /upload/jobs/{job_id}/review"""
    confirmed_columns: List[str]
