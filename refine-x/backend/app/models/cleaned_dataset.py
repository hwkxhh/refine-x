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

    # AI Classification flags — pending-review items for columns where AI
    # confidence was below 0.85 (medium) or below 0.60 (low). Includes conflict
    # between AI classification and HtypeDetector for user confirmation.
    ai_classification_flags = Column(JSON, nullable=True)

    # AI Formulas — Stage 2 formula assignments from classify_and_assign()
    # {column_name: ["FORMULA-ID-1", "FORMULA-ID-2", ...]}
    ai_formulas = Column(JSON, nullable=True)

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

    # Organizational & Product rules output (Session 9) — pending-review flags for
    # PROD, SKU, ORG, JOB, DEPT, REFNO, VER HTYPEs
    org_product_flags = Column(JSON, nullable=True)

    # Text & Technical rules output (Session 10) — pending-review flags for
    # TEXT, URL, IP, FILE HTYPEs
    text_technical_flags = Column(JSON, nullable=True)

    # Missing Value Decision Matrix output (Session 12) — flags for missing values
    # that require user confirmation or were auto-filled with derivation info
    missing_value_flags = Column(JSON, nullable=True)

    # Duplicate Resolution output (Session 13) — flags for duplicate records
    # that require user review (partial, fuzzy, temporal) or were auto-removed (exact)
    duplicate_flags = Column(JSON, nullable=True)

    # Analytical Formulas output (Session 14) — post-cleaning insights and metrics
    # including trends, correlations, distributions, forecasts, and derived analytics
    analytical_results = Column(JSON, nullable=True)

    # Conditional Validation output (Session 15) — cross-column validation flags
    # that require user review for logical inconsistencies between related columns
    conditional_flags = Column(JSON, nullable=True)

    # Medical Rules output (Session 16) — DIAG and PHYS formula flags
    # HTYPE-031 (Medical Diagnosis) is HIGH-SENSITIVITY PII - restricted export
    # HTYPE-032 (Physical Measurement) includes BMI derivation and validation
    medical_flags = Column(JSON, nullable=True)

    # Derived Metrics — computed columns added post-cleaning
    # [{name, label, htype, is_derived, source_columns, valid_values, domain_hint}]
    derived_metrics_info = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("UploadJob", back_populates="cleaned_dataset")
