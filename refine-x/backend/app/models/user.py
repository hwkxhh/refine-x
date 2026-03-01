from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    upload_jobs = relationship("UploadJob", back_populates="user")
    annotations = relationship("Annotation", back_populates="user")
    comparison_jobs = relationship("ComparisonJob", back_populates="user")
