from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Chart(Base):
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("upload_jobs.id"), nullable=False)
    chart_type = Column(String, nullable=False)  # line|bar|scatter|pie|grouped_bar
    x_header = Column(String, nullable=False)
    y_header = Column(String, nullable=True)      # nullable for pie charts
    title = Column(String, nullable=False)
    config = Column(JSON, nullable=True)          # colors, labels, etc.
    data = Column(JSON, nullable=False)           # Recharts-compatible data array
    is_recommended = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("UploadJob", back_populates="charts")
    insights = relationship("Insight", back_populates="chart")
    annotations = relationship("Annotation", back_populates="chart")
