import io
import math
from datetime import datetime

import numpy as np
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
from app.services.column_relevance import evaluate_column_relevance
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


def _to_python(obj):
    """
    Recursively convert numpy scalar types, pandas Timestamps, and
    non-finite floats to native Python types so that PostgreSQL's JSON
    serialiser never chokes.
    """
    import pandas as pd
    if isinstance(obj, dict):
        return {k: _to_python(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_python(v) for v in obj]
    # pandas Timestamp / NaT
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat() if not pd.isnull(obj) else None
    if isinstance(obj, type(pd.NaT)):
        return None
    # numpy types
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return [_to_python(v) for v in obj.tolist()]
    # plain float NaN/Inf
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    # datetime / date objects from stdlib
    import datetime as _dt
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()
    return obj


# ============================================================================
# TIERED CONFIDENCE THRESHOLDS FOR AI CLASSIFICATION
# ============================================================================
# >= 0.85: AI classification applies automatically
# 0.60 - 0.84: Check HtypeDetector agreement; if disagree → PendingReview
# < 0.60: Always create PendingReview for manual confirmation

AI_CONFIDENCE_HIGH = 0.85     # Auto-apply AI classification
AI_CONFIDENCE_LOW = 0.60      # Below this → always PendingReview


# ============================================================================
# HELPER: Load file bytes into a DataFrame
# ============================================================================

def _load_dataframe(file_bytes: bytes, file_type: str):
    """
    Parse raw file bytes into a DataFrame and a list of excel/headerless flags.
    Returns (df, excel_flags).
    """
    _excel_flags = []

    if file_type in ("csv", "txt"):
        # Error 12: encoding fallback — try UTF-8 first, fall back to latin-1
        # Error 13: sep=None + engine="python" auto-detects the delimiter
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding="latin-1")
    elif file_type in ("xlsx", "xls"):
        # Error 18: pick the sheet with the most rows; flag all sheet names
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        sheet_names = xl.sheet_names
        best_sheet = sheet_names[0]
        best_count = 0
        for sname in sheet_names:
            try:
                tmp_df = xl.parse(sname, header=None)
                if len(tmp_df) > best_count:
                    best_count = len(tmp_df)
                    best_sheet = sname
            except Exception:
                continue
        df = xl.parse(best_sheet)
        if len(sheet_names) > 1:
            _excel_flags.append({
                "flag_type": "EXCEL_MULTI_SHEET",
                "selected_sheet": best_sheet,
                "all_sheets": sheet_names,
                "message": (
                    f"File has {len(sheet_names)} sheets: {sheet_names}. "
                    f"Sheet '{best_sheet}' (most rows: {best_count}) was used. "
                    "Re-upload if a different sheet is needed."
                ),
                "pending_review": True,
            })
    else:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding="latin-1")

    return df, _excel_flags


def _detect_headerless(file_bytes: bytes, file_type: str, df, _excel_flags: list):
    """
    Error 17: if >= 70% of column names look numeric the file has no header row.
    Re-reads with header=None and auto-generates col_0, col_1, …
    Returns (df, _excel_flags) — potentially mutated.
    """
    if file_type in ("csv", "txt") and len(df.columns) > 0:
        col_names = [str(c) for c in df.columns]
        numeric_header_count = sum(
            1 for c in col_names
            if c.strip().lstrip("-").replace(".", "").isdigit()
        )
        if numeric_header_count / len(col_names) >= 0.7:
            try:
                df = pd.read_csv(
                    io.BytesIO(file_bytes), sep=None, engine="python",
                    encoding="utf-8", header=None,
                )
            except UnicodeDecodeError:
                df = pd.read_csv(
                    io.BytesIO(file_bytes), sep=None, engine="python",
                    encoding="latin-1", header=None,
                )
            df.columns = [f"col_{i}" for i in range(len(df.columns))]
            _excel_flags.append({
                "flag_type": "HEADERLESS_FILE_DETECTED",
                "message": (
                    "No header row detected — column names auto-generated as "
                    "col_0, col_1, … Please confirm or rename columns."
                ),
                "pending_review": True,
            })
    return df, _excel_flags


def _run_steps_1_through_4(job_id, job, db, file_bytes):
    """
    Shared helper: run Steps 1-4 (Load → Global → Struct) and return
    all intermediate state needed by both Phase 1 and Phase 2.
    """
    df, _excel_flags = _load_dataframe(file_bytes, job.file_type)
    df, _excel_flags = _detect_headerless(file_bytes, job.file_type, df, _excel_flags)

    # ── Normalise column names to plain Python str ────────────────
    # Prevents 'numpy.int64 has no attribute lower' across all downstream
    # rule engines (GlobalRules, StructRules, HtypeDetector, etc.)
    df.columns = [str(c) for c in df.columns]

    original_row_count = len(df)

    # ── GLOBAL rules (Session 1) ──────────────────────────────────
    global_runner = GlobalRules(job_id=job_id, df=df, db=db)
    global_summary = global_runner.run_all()
    df = global_runner.df
    global_flags = global_runner.flags
    pii_tags = global_summary.get("pii_tags", {})

    # ── STRUCT rules (Session 2) ──────────────────────────────────
    struct_runner = StructRules(
        job_id=job_id,
        df=df,
        db=db,
        file_bytes=file_bytes,
        file_type=job.file_type,
    )
    struct_summary = struct_runner.run_all()
    df = struct_runner.df
    struct_flags = _excel_flags + struct_runner.flags

    return {
        "df": df,
        "original_row_count": original_row_count,
        "global_summary": global_summary,
        "global_flags": global_flags,
        "pii_tags": pii_tags,
        "struct_summary": struct_summary,
        "struct_flags": struct_flags,
    }


# ============================================================================
# PHASE 1 — Steps 1-4 + Column Relevance Gate  (pauses at awaiting_review)
# ============================================================================

@celery_app.task(bind=True)
def process_csv_file(self, job_id: int):
    """
    Background task — PHASE 1:
      1. Download file from MinIO
      2. Run GLOBAL rules (Session 1 — cell/column/row hygiene)
      3. Run STRUCT rules (Session 2 — shape, layout, header alignment)
      4. Run Column Relevance Gate (GPT-4o column assessment)
      5. Pause: set status="awaiting_review" and persist result

    The pipeline STOPS here until the user confirms columns via
    POST /upload/jobs/{job_id}/review, which triggers resume_pipeline_after_review().
    """
    db = SessionLocal()
    job = None
    try:
        job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
        if not job:
            return {"error": f"Job {job_id} not found"}

        job.status = "processing"
        db.commit()

        # ── Steps 1-4 ────────────────────────────────────────────────
        file_bytes = storage_service.download_file(job.file_path)
        state = _run_steps_1_through_4(job_id, job, db, file_bytes)
        df = state["df"]

        # ── Column Relevance Gate (NEW — runs after Struct, before AI) ─
        sample_rows = df.head(5).fillna("").to_dict(orient="records")
        str_columns = [str(c) for c in df.columns.tolist()]
        try:
            relevance_result = evaluate_column_relevance(
                columns=str_columns,
                sample_rows=sample_rows,
                filename=job.filename,
            )
        except Exception as e:
            # If the GPT call fails, keep all columns and skip the gate
            print(f"Column relevance gate failed for job {job_id}: {e}")
            relevance_result = {
                "overall_verdict": "useful",
                "reason": "Column relevance evaluation failed — all columns kept by default.",
                "columns": [
                    {"name": col, "recommendation": "keep", "reason": "default — AI call failed"}
                    for col in str_columns
                ],
            }

        # ── Pause: persist and await user review ──────────────────────
        job.column_relevance_result = relevance_result
        job.status = "awaiting_review"
        db.commit()

        return {
            "job_id": job_id,
            "status": "awaiting_review",
            "column_relevance_result": relevance_result,
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


# ============================================================================
# PHASE 2 — Steps 5+ (AI Classification → Cleaning → Analytics → Persist)
# ============================================================================

@celery_app.task(bind=True)
def resume_pipeline_after_review(self, job_id: int):
    """
    Background task — PHASE 2 (triggered after user confirms columns):
      5. Replay Steps 1-4 (deterministic), then apply column filter
      6. Run Stage 1+2 AI Classification (GPT-4o HTYPE + Formulas)
      7. Run HTYPE Detection (deterministic fallback)
      8. Tiered Confidence Merge
      9. Sessions 4–10, 12–13, 15–16 (HTYPE-specific cleaning)
     10. DataCleaningPipeline (generic 4-phase pass)
     11. Quality score
     12. Analytical Formulas (Session 14)
     13. Persist CleanedDataset + cache + update UploadJob
    """
    db = SessionLocal()
    job = None
    try:
        job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
        if not job:
            return {"error": f"Job {job_id} not found"}

        if job.status != "awaiting_review":
            return {"error": f"Job {job_id} is not awaiting review (status={job.status})"}

        confirmed_columns = job.confirmed_columns
        if not confirmed_columns:
            return {"error": f"Job {job_id} has no confirmed_columns set"}

        job.status = "processing"
        db.commit()

        # ── Replay Steps 1-4 to reconstruct df ───────────────────────
        # (We don't cache the intermediate df to avoid Redis bloat;
        #  GlobalRules + StructRules are fast and deterministic.)
        file_bytes = storage_service.download_file(job.file_path)
        state = _run_steps_1_through_4(job_id, job, db, file_bytes)
        df = state["df"]
        original_row_count = state["original_row_count"]
        global_summary = state["global_summary"]
        global_flags = state["global_flags"]
        pii_tags = state["pii_tags"]
        struct_summary = state["struct_summary"]
        struct_flags = state["struct_flags"]

        # ── Apply Column Filter ───────────────────────────────────────
        # Keep only the columns the user confirmed.
        valid_cols = [c for c in confirmed_columns if c in df.columns]
        if not valid_cols:
            raise ValueError("None of the confirmed columns exist in the DataFrame")
        df = df[valid_cols]

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
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        pi_summary = pi_runner.run_all()
        df = pi_runner.df
        pi_flags = pi_runner.flags

        # ── Date & Time Rules (Session 5) ─────────────────────────────
        # Applies HTYPE-specific cleaning for DATE, TIME, DTM, DUR, FISC
        # columns based on the HTYPE classification from Session 3.
        dt_runner = DateTimeRules(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        dt_summary = dt_runner.run_all()
        df = dt_runner.df
        dt_flags = dt_runner.flags

        # ── Contact & Location Rules (Session 6) ─────────────────────
        # Applies HTYPE-specific cleaning for PHONE, EMAIL, ADDR, CITY,
        # CNTRY, POST, GEO columns based on HTYPE classification.
        cl_runner = ContactLocationRules(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        cl_summary = cl_runner.run_all()
        df = cl_runner.df
        cl_flags = cl_runner.flags

        # ── Numeric & Financial Rules (Session 7) ────────────────────
        # Applies HTYPE-specific cleaning for AMT, QTY, PCT, SCORE,
        # CUR, RANK, CALC columns based on HTYPE classification.
        nf_runner = NumericFinancialRules(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        nf_summary = nf_runner.run_all()
        df = nf_runner.df
        nf_flags = nf_runner.flags

        # ── Boolean, Category & Status Rules (Session 8) ─────────────
        # Applies HTYPE-specific cleaning for BOOL, CAT, STAT, SURV,
        # MULTI columns based on HTYPE classification.
        bc_runner = BooleanCategoryRules(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        bc_summary = bc_runner.run_all()
        df = bc_runner.df
        bc_flags = bc_runner.flags

        # ── Organizational & Product Rules (Session 9) ───────────────
        # Applies HTYPE-specific cleaning for PROD, SKU, ORG, JOB,
        # DEPT, REFNO, VER columns based on HTYPE classification.
        op_runner = OrgProductRules(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        op_summary = op_runner.run_all()
        df = op_runner.df
        op_flags = op_runner.flags

        # ── Text & Technical Rules (Session 10) ──────────────────────
        # Applies HTYPE-specific cleaning for TEXT, URL, IP, FILE
        # columns based on HTYPE classification.
        tt_runner = TextTechnicalRules(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        tt_summary = tt_runner.run_all()
        df = tt_runner.df
        tt_flags = tt_runner.flags

        # ── Missing Value Decision Matrix (Session 12) ───────────────
        # Analyzes missing values and auto-fills derivable values,
        # suggests medium-confidence fills, prompts for unknowns.
        mv_runner = MissingValueMatrix(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        mv_summary = mv_runner.run_all()
        df = mv_runner.df
        mv_flags = mv_runner.flags

        # ── Duplicate Resolution (Session 13) ────────────────────────
        # Detects exact, partial, fuzzy, and temporal duplicates.
        # Auto-removes exact duplicates, flags others for user review.
        dup_runner = DuplicateResolution(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        dup_summary = dup_runner.run_all()
        df = dup_runner.df
        dup_flags = dup_runner.flags

        # ── Conditional Validation (Session 15) ──────────────────────
        # Cross-column validation for logical consistency: status-date
        # dependencies, date sequences, age-DOB, score-pass, referential
        # integrity, and total=sum validations. Flags issues for review.
        cond_runner = ConditionalValidation(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        cond_summary = cond_runner.run_all()
        cond_flags = cond_runner.flags

        # ── Medical Rules (Session 16) ───────────────────────────────
        # HTYPE-031 (Medical Diagnosis): HIGH-SENSITIVITY PII - title case,
        # ICD validation, abbreviation expansion (HTN, DM, MI, etc.)
        # HTYPE-032 (Physical Measurement): unit extraction, imperial-metric
        # conversion, BMI derivation and categorization, range validation.
        med_runner = MedicalRules(
            job_id=job_id, df=df, db=db, htype_map=htype_map,
        )
        med_summary = med_runner.run_all()
        df = med_runner.df
        med_flags = med_runner.flags

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
            job_id=job_id, df=cleaned_df, db=db, htype_map=htype_map,
        )
        analytics_results = analytics_runner.run_all()

        # ── Build per-column metadata ─────────────────────────────────
        col_meta = {}
        for col in cleaned_df.columns:
            series = cleaned_df[col]
            raw_sample = series.dropna().head(3).tolist()
            # Convert every sample value through _to_python so Timestamps,
            # numpy scalars, NaN and Inf are all safe for JSON storage.
            safe_sample = [_to_python(v) for v in raw_sample]
            col_meta[col] = {
                "dtype": str(series.dtype),
                "null_count": int(series.isnull().sum()),
                "unique_count": int(series.nunique()),
                "sample": safe_sample,
            }

        # ── Persist CleanedDataset ────────────────────────────────────
        existing = db.query(CleanedDataset).filter(CleanedDataset.job_id == job_id).first()
        if existing:
            db.delete(existing)
            db.flush()

        cleaned_record = CleanedDataset(
            job_id=job_id,
            column_metadata=_to_python(col_meta),
            row_count_original=original_row_count,
            row_count_cleaned=len(cleaned_df),
            quality_score=quality,
            cleaning_summary=_to_python(summary),
            global_flags=_to_python(global_flags),
            pii_tags=_to_python(pii_tags),
            htype_map=_to_python(htype_map),
            ai_classification_flags=_to_python(ai_flags),
            ai_formulas=_to_python(ai_formulas),
            struct_flags=_to_python(struct_flags),
            personal_identity_flags=_to_python(pi_flags),
            date_time_flags=_to_python(dt_flags),
            contact_location_flags=_to_python(cl_flags),
            numeric_financial_flags=_to_python(nf_flags),
            boolean_category_flags=_to_python(bc_flags),
            org_product_flags=_to_python(op_flags),
            text_technical_flags=_to_python(tt_flags),
            missing_value_flags=_to_python(mv_flags),
            duplicate_flags=_to_python(dup_flags),
            analytical_results=_to_python(analytics_results),
            conditional_flags=_to_python(cond_flags),
            medical_flags=_to_python(med_flags),
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
