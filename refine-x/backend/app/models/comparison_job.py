from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ComparisonJob(Base):
    __tablename__ = "comparison_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id_1 = Column(Integer, ForeignKey("upload_jobs.id"), nullable=False)
    job_id_2 = Column(Integer, ForeignKey("upload_jobs.id"), nullable=False)
    # Proposed or confirmed column mapping: {df1_col: df2_col}
    header_mapping = Column(JSON, nullable=True)
    # Computed deltas after confirm: [{column, period1_value, period2_value, change_pct}]
    deltas = Column(JSON, nullable=True)
    # Significant changes: [{column, change_pct}]
    significant_changes = Column(JSON, nullable=True)
    status = Column(String, default="pending")   # pending|completed|failed
    ai_insight = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="comparison_jobs")
