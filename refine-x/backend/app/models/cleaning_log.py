from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class CleaningLog(Base):
    __tablename__ = "cleaning_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("upload_jobs.id"), nullable=False)

    row_index = Column(Integer, nullable=True)       # which row (None = column-level change)
    column_name = Column(String, nullable=True)       # which column

    # Action types: remove_duplicate | fill_missing | flag_outlier |
    #               normalize_column_name | remove_empty_column |
    #               convert_date | bucket_age | (any GLOBAL/HTYPE formula ID action)
    action = Column(String, nullable=False)

    original_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    reason = Column(String, nullable=False)

    # Formula traceability — Formula ID from rulebook (e.g. GLOBAL-03, FNAME-01)
    formula_id = Column(String, nullable=True, index=True)
    # True = auto-applied silently; False = pending user review / ask-first
    was_auto_applied = Column(Boolean, nullable=True, default=True)

    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("UploadJob", back_populates="cleaning_logs")
