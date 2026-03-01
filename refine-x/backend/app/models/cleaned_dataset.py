from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class CleanedDataset(Base):
    __tablename__ = "cleaned_datasets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("upload_jobs.id"), unique=True, nullable=False)

    # Per-column metadata: {col_name: {dtype, null_count, unique_count, sample}}
    column_metadata = Column(JSON, nullable=True)

    # Row counts
    row_count_original = Column(Integer, nullable=True)
    row_count_cleaned = Column(Integer, nullable=True)

    # Quality score
    quality_score = Column(Float, nullable=True)

    # Cleaning summary: {duplicates_removed, outliers_flagged, missing_filled,
    #                     columns_renamed, columns_dropped, dates_converted, ages_bucketed}
    cleaning_summary = Column(JSON, nullable=True)

    # GLOBAL rules output — pending-review flags surfaced to the frontend
    # List of {formula_id, flag_type, description, affected_columns, suggested_action}
    global_flags = Column(JSON, nullable=True)

    # HTYPE detection map — {column_name: htype_code}  (populated by Session 3 engine)
    htype_map = Column(JSON, nullable=True)

    # PII tags — {column_name: {level, label}}  (populated by GLOBAL-10)
    pii_tags = Column(JSON, nullable=True)

    # STRUCT rules output — pending-review flags from Session 2 structural checks
    # List of {formula_id, flag_type, description, affected_columns, suggested_action}
    struct_flags = Column(JSON, nullable=True)

    # Personal Identity rules output (Session 4) — pending-review flags for
    # FNAME, SNAME, UID, AGE, GEN HTYPEs
    personal_identity_flags = Column(JSON, nullable=True)

    # Date & Time rules output (Session 5) — pending-review flags for
    # DATE, TIME, DTM, DUR, FISC HTYPEs
    date_time_flags = Column(JSON, nullable=True)

    # Contact & Location rules output (Session 6) — pending-review flags for
    # PHONE, EMAIL, ADDR, CITY, CNTRY, POST, GEO HTYPEs
    contact_location_flags = Column(JSON, nullable=True)

    # Numeric & Financial rules output (Session 7) — pending-review flags for
    # AMT, QTY, PCT, SCORE, CUR, RANK, CALC HTYPEs
    numeric_financial_flags = Column(JSON, nullable=True)

    # Boolean, Category & Status rules output (Session 8) — pending-review flags for
    # BOOL, CAT, STAT, SURV, MULTI HTYPEs
    boolean_category_flags = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("UploadJob", back_populates="cleaned_dataset")
