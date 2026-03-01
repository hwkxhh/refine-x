from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.upload_job import UploadJob
from app.models.user import User
from app.schemas.upload import UploadJobResponse, UploadJobListResponse, JobStatusResponse
from app.services.auth import get_current_user
from app.services.storage import storage_service
from app.tasks.process_csv import process_csv_file

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadJobResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a CSV or Excel file. Returns a job record immediately; processing runs in background."""
    validation = storage_service.validate_file(file)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    job = UploadJob(
        user_id=current_user.id,
        filename=file.filename,
        file_path="",
        file_size=validation["file_size"],
        file_type=validation["file_type"],
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        file_path = storage_service.upload_file(file, job.id)
        job.file_path = file_path
        db.commit()
        db.refresh(job)
    except Exception as e:
        db.delete(job)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    process_csv_file.delay(job.id)

    return job


@router.get("/jobs", response_model=List[UploadJobListResponse])
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all upload jobs belonging to the current user."""
    return (
        db.query(UploadJob)
        .filter(UploadJob.user_id == current_user.id)
        .order_by(UploadJob.created_at.desc())
        .all()
    )


@router.get("/jobs/{job_id}", response_model=UploadJobResponse)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full details of a specific upload job."""
    job = db.query(UploadJob).filter(
        UploadJob.id == job_id, UploadJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll processing status of a job (pending → processing → completed/failed)."""
    job = db.query(UploadJob).filter(
        UploadJob.id == job_id, UploadJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress_map = {"pending": 0, "processing": 50, "completed": 100, "failed": 0}

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=progress_map.get(job.status, 0),
        quality_score=job.quality_score,
        row_count=job.row_count,
        error_message=job.error_message,
    )


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a job and its associated file from MinIO."""
    job = db.query(UploadJob).filter(
        UploadJob.id == job_id, UploadJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.file_path:
        storage_service.delete_file(job.file_path)

    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully"}
