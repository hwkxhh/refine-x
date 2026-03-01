from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # File metadata
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)  # 'csv' or 'xlsx'

    # Processing status
    status = Column(String, default="pending")  # pending/processing/completed/failed
    error_message = Column(String, nullable=True)

    # Results (filled after processing)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    quality_score = Column(Float, nullable=True)  # 0-100

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="upload_jobs")
    cleaned_dataset = relationship("CleanedDataset", back_populates="job", uselist=False)
    cleaning_logs = relationship("CleaningLog", back_populates="job")
    user_goal = relationship("UserGoal", back_populates="job", uselist=False)
    charts = relationship("Chart", back_populates="job")
    insights = relationship("Insight", back_populates="job")
