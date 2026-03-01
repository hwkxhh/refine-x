from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UploadJobResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    file_type: str
    status: str
    quality_score: Optional[float] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
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
