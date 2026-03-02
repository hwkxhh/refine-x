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
from app.services.ai_analysis import classify_and_assign  # Combined Stage 1+2
from app.services.personal_identity_rules import PersonalIdentityRules
from app.services.date_time_rules import DateTimeRules
from app.services.contact_location_rules import ContactLocationRules
from app.services.numeric_financial_rules import NumericFinancialRules
from app.services.boolean_category_rules import BooleanCategoryRules
from app.services.org_product_rules import OrgProductRules
from app.services.text_technical_rules import TextTechnicalRules
from app.services.missing_value_matrix import MissingValueMatrix
from app.services.duplicate_resolution import DuplicateResolution
from app.services.conditional_validation import ConditionalValidation
from app.services.medical_rules import MedicalRules
from app.services.analytical_formulas import AnalyticalFormulas
from app.services.cleaning import DataCleaningPipeline
from app.services.quality import calculate_quality_score
from app.services.cache import cache_dataframe

# ============================================================================
# TIERED CONFIDENCE THRESHOLDS FOR AI CLASSIFICATION
# ============================================================================
# >= 0.85: AI classification applies automatically
# 0.60 - 0.84: Check HtypeDetector agreement; if disagree → PendingReview
# < 0.60: Always create PendingReview for manual confirmation

AI_CONFIDENCE_HIGH = 0.85     # Auto-apply AI classification
AI_CONFIDENCE_LOW = 0.60      # Below this → always PendingReview


@celery_app.task(bind=True)
def process_csv_file(self, job_id: int):
    """
    Background task:
      1. Download file from MinIO
      2. Run GLOBAL rules (Session 1 — cell/column/row hygiene)
      3. Run STRUCT rules (Session 2 — shape, layout, header alignment)
      4. Run Stage 1 AI Classification (primary HTYPE source)
      5. Run HTYPE cleaning pipeline (Sessions 4+)
      6. Calculate quality score
      7. Cache cleaned DataFrame in Redis
      8. Persist CleanedDataset + CleaningLog entries
      9. Update UploadJob with final metrics
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

        # ── Stage 1+2 AI Classification (Combined GPT Call) ─────────
        # GPT-4o classifies each column and assigns formulas in one call.
        # Results are validated against tiered confidence thresholds.
        sample_rows = df.head(5).fillna("").to_dict(orient="records")
        ai_classification = {}
        ai_formulas = {}
        ai_flags = []  # PendingReview items for uncertain classifications
        
        try:
            ai_result = classify_and_assign(
                columns=df.columns.tolist(),
                sample_rows=sample_rows,
                filename=job.filename,
            )
            ai_classification = ai_result.get("columns", {})
            
            # Extract formulas for Stage 2
            for col, data in ai_classification.items():
                ai_formulas[col] = data.get("formulas", [])
                
        except Exception as e:
            # If AI classification fails, continue with HtypeDetector only
            print(f"AI classification failed for job {job_id}: {e}")

        # ── HTYPE Detection (Session 3 — Fallback) ────────────────────
        # HtypeDetector runs for all columns. Serves as deterministic
        # fallback when AI confidence is low or AI/HtypeDetector disagree.
        htype_detector = HtypeDetector()
        htype_report = htype_detector.get_detection_report(df)
        htype_map = htype_report["htype_map"]  # Fallback HTYPEs
        
        # ── Tiered Confidence Merge ───────────────────────────────────
        # Merge AI classification with HtypeDetector using tiered thresholds:
        #   >= 0.85: AI classification applies automatically
        #   0.60-0.84: Check HtypeDetector agreement; disagree → PendingReview
        #   < 0.60: Always create PendingReview
        
        for col, ai_data in ai_classification.items():
            if col not in htype_map:
                continue
                
            ai_htype = ai_data.get("htype", "HTYPE-000")
            ai_confidence = ai_data.get("confidence", 0.0)
            detector_htype = htype_map[col]
            
            if ai_confidence >= AI_CONFIDENCE_HIGH:
                # High confidence: use AI classification directly
                htype_map[col] = ai_htype
                
            elif ai_confidence >= AI_CONFIDENCE_LOW:
                # Medium confidence: check agreement with HtypeDetector
                if ai_htype == detector_htype:
                    # AI and HtypeDetector agree → use the classification
                    htype_map[col] = ai_htype
                else:
                    # AI and HtypeDetector disagree → create PendingReview
                    ai_flags.append({
                        "flag_type": "HTYPE_CLASSIFICATION_CONFLICT",
                        "column": col,
                        "ai_htype": ai_htype,
                        "ai_confidence": ai_confidence,
                        "detector_htype": detector_htype,
                        "message": (
                            f"Column '{col}' classification uncertain. "
                            f"AI suggests {ai_htype} (confidence: {ai_confidence:.0%}), "
                            f"HtypeDetector suggests {detector_htype}. "
                            f"Please confirm the correct column type."
                        ),
                        "pending_review": True,
                    })
                    # Keep HtypeDetector result until user confirms
                    # (already in htype_map, no action needed)
                    
            else:
                # Low confidence: always create PendingReview
                ai_flags.append({
                    "flag_type": "HTYPE_CLASSIFICATION_LOW_CONFIDENCE",
                    "column": col,
                    "ai_htype": ai_htype,
                    "ai_confidence": ai_confidence,
                    "detector_htype": detector_htype,
                    "message": (
                        f"Column '{col}' could not be confidently classified. "
                        f"AI confidence: {ai_confidence:.0%}. "
                        f"Using HtypeDetector default ({detector_htype}). "
                        f"Please manually confirm the correct column type."
                    ),
                    "pending_review": True,
                })
                # Keep HtypeDetector result (already in htype_map)

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

        # ── Organizational & Product Rules (Session 9) ───────────────
        # Applies HTYPE-specific cleaning for PROD, SKU, ORG, JOB,
        # DEPT, REFNO, VER columns based on HTYPE classification.
        op_runner = OrgProductRules(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        op_summary = op_runner.run_all()
        df = op_runner.df              # use org/product-cleaned df
        op_flags = op_runner.flags     # pending-review items for frontend

        # ── Text & Technical Rules (Session 10) ──────────────────────
        # Applies HTYPE-specific cleaning for TEXT, URL, IP, FILE
        # columns based on HTYPE classification.
        tt_runner = TextTechnicalRules(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        tt_summary = tt_runner.run_all()
        df = tt_runner.df              # use text/technical-cleaned df
        tt_flags = tt_runner.flags     # pending-review items for frontend

        # ── Missing Value Decision Matrix (Session 12) ───────────────
        # Analyzes missing values and auto-fills derivable values,
        # suggests medium-confidence fills, prompts for unknowns.
        mv_runner = MissingValueMatrix(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        mv_summary = mv_runner.run_all()
        df = mv_runner.df              # use missing-value-processed df
        mv_flags = mv_runner.flags     # pending-review items for frontend

        # ── Duplicate Resolution (Session 13) ────────────────────────
        # Detects exact, partial, fuzzy, and temporal duplicates.
        # Auto-removes exact duplicates, flags others for user review.
        dup_runner = DuplicateResolution(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        dup_summary = dup_runner.run_all()
        df = dup_runner.df             # use duplicate-resolved df
        dup_flags = dup_runner.flags   # pending-review items for frontend

        # ── Conditional Validation (Session 15) ──────────────────────
        # Cross-column validation for logical consistency: status-date
        # dependencies, date sequences, age-DOB, score-pass, referential
        # integrity, and total=sum validations. Flags issues for review.
        cond_runner = ConditionalValidation(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        cond_summary = cond_runner.run_all()
        cond_flags = cond_runner.flags  # pending-review items for frontend

        # ── Medical Rules (Session 16) ───────────────────────────────
        # HTYPE-031 (Medical Diagnosis): HIGH-SENSITIVITY PII - title case,
        # ICD validation, abbreviation expansion (HTN, DM, MI, etc.)
        # HTYPE-032 (Physical Measurement): unit extraction, imperial-metric
        # conversion, BMI derivation and categorization, range validation.
        med_runner = MedicalRules(
            job_id=job_id,
            df=df,
            db=db,
            htype_map=htype_map,
        )
        med_summary = med_runner.run_all()
        df = med_runner.df             # use medical-processed df
        med_flags = med_runner.flags   # pending-review items for frontend

        # Merge medical PII tags with existing PII tags
        pii_tags.update(med_summary.get("pii_tags", {}))

        # ── Run HTYPE cleaning pipeline ───────────────────────────────
        pipeline = DataCleaningPipeline(job_id=job_id, df=df, db=db)
        summary = pipeline.run_all()
        cleaned_df = pipeline.df

        # ── Merge GlobalRules renames into summary ────────────────────
        # GlobalRules normalises column names (GLOBAL-03) before the
        # DataCleaningPipeline runs, so the pipeline sees 0 renames.
        # Add the GlobalRules rename count here.
        global_renames = global_summary.get("columns_renamed", {})
        summary["columns_renamed"] = (
            summary.get("columns_renamed", 0)
            + (len(global_renames) if isinstance(global_renames, dict) else int(global_renames))
        )
        # Merge row_count_original into summary for completeness
        summary["row_count_original"] = original_row_count
        summary["row_count_cleaned"] = len(cleaned_df)

        # ── Quality score ─────────────────────────────────────────────
        quality = calculate_quality_score(cleaned_df, original_row_count)

        # ── Analytical Formulas (Session 14) ─────────────────────────
        # Post-cleaning analysis: trends, correlations, distributions,
        # forecasts, and derived metrics for visualization and reporting.
        analytics_runner = AnalyticalFormulas(
            job_id=job_id,
            df=cleaned_df,
            db=db,
            htype_map=htype_map,
        )
        analytics_results = analytics_runner.run_all()

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
            ai_classification_flags=ai_flags,  # AI classification pending-review items
            ai_formulas=ai_formulas,         # Stage 2 formula assignments
            struct_flags=struct_flags,       # STRUCT rules pending-review items
            personal_identity_flags=pi_flags,  # Session 4 pending-review items
            date_time_flags=dt_flags,        # Session 5 pending-review items
            contact_location_flags=cl_flags, # Session 6 pending-review items
            numeric_financial_flags=nf_flags, # Session 7 pending-review items
            boolean_category_flags=bc_flags,  # Session 8 pending-review items
            org_product_flags=op_flags,       # Session 9 pending-review items
            text_technical_flags=tt_flags,   # Session 10 pending-review items
            missing_value_flags=mv_flags,    # Session 12 pending-review items
            duplicate_flags=dup_flags,       # Session 13 pending-review items
            analytical_results=analytics_results,  # Session 14 post-cleaning analytics
            conditional_flags=cond_flags,    # Session 15 cross-column validation
            medical_flags=med_flags,         # Session 16 medical DIAG/PHYS rules
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
            "ai_classification_flags_count": len(ai_flags),
            "ai_formulas": ai_formulas,
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
