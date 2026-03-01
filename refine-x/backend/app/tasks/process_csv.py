import io
from datetime import datetime

import pandas as pd
from celery_app import celery_app
from app.database import SessionLocal
from app.models.upload_job import UploadJob
from app.models.cleaned_dataset import CleanedDataset
from app.services.storage import storage_service
from app.services.global_rules import GlobalRules
from app.services.struct_rules import StructRules
from app.services.htype_detector import HtypeDetector
from app.services.personal_identity_rules import PersonalIdentityRules
from app.services.date_time_rules import DateTimeRules
from app.services.contact_location_rules import ContactLocationRules
from app.services.numeric_financial_rules import NumericFinancialRules
from app.services.boolean_category_rules import BooleanCategoryRules
from app.services.cleaning import DataCleaningPipeline
from app.services.quality import calculate_quality_score
from app.services.cache import cache_dataframe


@celery_app.task(bind=True)
def process_csv_file(self, job_id: int):
    """
    Background task:
      1. Download file from MinIO
      2. Run GLOBAL rules (Session 1 — cell/column/row hygiene)
      3. Run STRUCT rules (Session 2 — shape, layout, header alignment)
      4. Run HTYPE cleaning pipeline (Sessions 4+)
      5. Calculate quality score
      6. Cache cleaned DataFrame in Redis
      7. Persist CleanedDataset + CleaningLog entries
      8. Update UploadJob with final metrics
    """
    db = SessionLocal()
    job = None
    try:
        job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
        if not job:
            return {"error": f"Job {job_id} not found"}

        job.status = "processing"
        db.commit()

        # ── Load file ────────────────────────────────────────────────
        file_bytes = storage_service.download_file(job.file_path)
        if job.file_type in ("csv", "txt"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif job.file_type in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))

        original_row_count = len(df)

        # ── GLOBAL rules (Session 1) ──────────────────────────────────
        # Must run on the raw df BEFORE any HTYPE-specific cleaning.
        global_runner = GlobalRules(job_id=job_id, df=df, db=db)
        global_summary = global_runner.run_all()
        df = global_runner.df          # use globally-cleaned df downstream
        global_flags = global_runner.flags  # pending-review items for frontend
        pii_tags = global_summary.get("pii_tags", {})

        # ── STRUCT rules (Session 2) ──────────────────────────────────
        # Fixes macro-level structural issues (header offset, group-label
        # forward-fill) and flags wide/transposed/multi-sheet layouts.
        struct_runner = StructRules(
            job_id=job_id,
            df=df,
            db=db,
            file_bytes=file_bytes,
            file_type=job.file_type,
        )
        struct_summary = struct_runner.run_all()
        df = struct_runner.df          # use structurally-corrected df
        struct_flags = struct_runner.flags

        # ── HTYPE Detection (Session 3) ───────────────────────────────
        # Classifies each column to one of 47 HTYPEs based on column name,
        # value patterns, and data distribution. This determines which
        # HTYPE-specific formulas apply in subsequent sessions.
        htype_detector = HtypeDetector()
        htype_report = htype_detector.get_detection_report(df)
        htype_map = htype_report["htype_map"]

        # ── Personal Identity Rules (Session 4) ──────────────────────
        # Applies HTYPE-specific cleaning for FNAME, SNAME, UID, AGE, GEN
        # columns based on the HTYPE classification from Session 3.
        pi_runner = PersonalIdentityRules(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        pi_summary = pi_runner.run_all()
        df = pi_runner.df              # use identity-cleaned df
        pi_flags = pi_runner.flags     # pending-review items for frontend

        # ── Date & Time Rules (Session 5) ─────────────────────────────
        # Applies HTYPE-specific cleaning for DATE, TIME, DTM, DUR, FISC
        # columns based on the HTYPE classification from Session 3.
        dt_runner = DateTimeRules(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        dt_summary = dt_runner.run_all()
        df = dt_runner.df              # use date/time-cleaned df
        dt_flags = dt_runner.flags     # pending-review items for frontend

        # ── Contact & Location Rules (Session 6) ─────────────────────
        # Applies HTYPE-specific cleaning for PHONE, EMAIL, ADDR, CITY,
        # CNTRY, POST, GEO columns based on HTYPE classification.
        cl_runner = ContactLocationRules(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        cl_summary = cl_runner.run_all()
        df = cl_runner.df              # use contact/location-cleaned df
        cl_flags = cl_runner.flags     # pending-review items for frontend

        # ── Numeric & Financial Rules (Session 7) ────────────────────
        # Applies HTYPE-specific cleaning for AMT, QTY, PCT, SCORE,
        # CUR, RANK, CALC columns based on HTYPE classification.
        nf_runner = NumericFinancialRules(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        nf_summary = nf_runner.run_all()
        df = nf_runner.df              # use numeric/financial-cleaned df
        nf_flags = nf_runner.flags     # pending-review items for frontend

        # ── Boolean, Category & Status Rules (Session 8) ─────────────
        # Applies HTYPE-specific cleaning for BOOL, CAT, STAT, SURV,
        # MULTI columns based on HTYPE classification.
        bc_runner = BooleanCategoryRules(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        bc_summary = bc_runner.run_all()
        df = bc_runner.df              # use boolean/category-cleaned df
        bc_flags = bc_runner.flags     # pending-review items for frontend

        # ── Run HTYPE cleaning pipeline ───────────────────────────────
        pipeline = DataCleaningPipeline(job_id=job_id, df=df, db=db)
        summary = pipeline.run_all()
        cleaned_df = pipeline.df

        # ── Quality score ─────────────────────────────────────────────
        quality = calculate_quality_score(cleaned_df, original_row_count)

        # ── Build per-column metadata ─────────────────────────────────
        col_meta = {}
        for col in cleaned_df.columns:
            series = cleaned_df[col]
            col_meta[col] = {
                "dtype": str(series.dtype),
                "null_count": int(series.isnull().sum()),
                "unique_count": int(series.nunique()),
                "sample": series.dropna().head(3).tolist(),
            }

        # ── Persist CleanedDataset ────────────────────────────────────
        existing = db.query(CleanedDataset).filter(CleanedDataset.job_id == job_id).first()
        if existing:
            db.delete(existing)
            db.flush()

        cleaned_record = CleanedDataset(
            job_id=job_id,
            column_metadata=col_meta,
            row_count_original=original_row_count,
            row_count_cleaned=len(cleaned_df),
            quality_score=quality,
            cleaning_summary=summary,
            global_flags=global_flags,       # GLOBAL rules pending-review items
            pii_tags=pii_tags,               # GLOBAL-10 PII classification
            htype_map=htype_map,             # Session 3 HTYPE classification
            struct_flags=struct_flags,       # STRUCT rules pending-review items
            personal_identity_flags=pi_flags,  # Session 4 pending-review items
            date_time_flags=dt_flags,        # Session 5 pending-review items
            contact_location_flags=cl_flags, # Session 6 pending-review items
            numeric_financial_flags=nf_flags, # Session 7 pending-review items
            boolean_category_flags=bc_flags,  # Session 8 pending-review items
            created_at=datetime.utcnow(),
        )
        db.add(cleaned_record)

        # ── Cache cleaned DataFrame in Redis ──────────────────────────
        cache_dataframe(job_id, cleaned_df)

        # ── Update UploadJob ──────────────────────────────────────────
        job.status = "completed"
        job.row_count = len(cleaned_df)
        job.column_count = len(cleaned_df.columns)
        job.quality_score = quality
        job.processed_at = datetime.utcnow()
        db.commit()

        return {
            "job_id": job_id,
            "status": "completed",
            "row_count": len(cleaned_df),
            "column_count": len(cleaned_df.columns),
            "quality_score": quality,
            "cleaning_summary": summary,
            "global_rules_applied": global_summary.get("global_rules_applied", []),
            "global_flags_count": len(global_flags),
            "pii_columns_found": len(pii_tags),
            "struct_rules_applied": struct_summary.get("struct_rules_applied", []),
            "struct_flags_count": len(struct_flags),
            "htype_map": htype_map,
            "htype_pii_columns": htype_report.get("pii_columns", []),
            "htype_high_sensitivity_columns": htype_report.get("high_sensitivity_columns", []),
            "htype_confidence_stats": htype_report.get("confidence_stats", {}),
            "personal_identity_rules_applied": pi_summary.get("personal_identity_rules_applied", []),
            "personal_identity_flags_count": len(pi_flags),
            "personal_identity_changes": pi_summary.get("total_changes", 0),
            "date_time_rules_applied": dt_summary.get("date_time_rules_applied", []),
            "date_time_flags_count": len(dt_flags),
            "date_time_changes": dt_summary.get("total_changes", 0),
        }

    except Exception as e:
        db.rollback()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        return {"error": str(e), "job_id": job_id}

    finally:
        db.close()


# Keep old test task for smoke-testing
@celery_app.task
def test_task(name: str):
    import time
    time.sleep(2)
    return {"status": "success", "message": f"Hello, {name}! Task completed."}
