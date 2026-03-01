from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class UserGoal(Base):
    __tablename__ = "user_goals"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("upload_jobs.id"), unique=True, nullable=False)
    goal_text = Column(String, nullable=False)
    # 'sales', 'performance', 'cost', 'marketing', 'custom'
    goal_category = Column(String, default="custom")
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("UploadJob", back_populates="user_goal")
