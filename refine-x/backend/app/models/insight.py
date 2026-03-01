from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("upload_jobs.id"), nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(String, nullable=False)        # low|medium|high
    confidence_score = Column(Float, nullable=False)   # 0.0-1.0
    recommendations = Column(JSON, nullable=True)       # [{action, reasoning}]
    created_at = Column(DateTime, default=datetime.utcnow)

    chart = relationship("Chart", back_populates="insights")
    job = relationship("UploadJob", back_populates="insights")
