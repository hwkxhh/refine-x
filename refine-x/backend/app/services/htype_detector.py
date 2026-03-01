"""
HTYPE Detection Engine — Session 3

Classifies each column in a DataFrame to one of 47 Header Types (HTYPEs)
based on column name keywords, value patterns, and data distribution.

Each HTYPE maps to a specific Formula Set for cleaning operations.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class HtypeMatch:
    """Result of HTYPE detection for a single column."""
    htype_code: str
    htype_name: str
    formula_set: str
    confidence: float  # 0.0 - 1.0
    match_reason: str
    is_pii: bool = False
    sensitivity_level: str = "low"  # low, medium, high


class HtypeDetector:
    """
    Detects Header Types (HTYPEs) for DataFrame columns.
    
    Detection Priority (from Appendix E):
    1. Exact column name match
    2. Partial keyword match in column name
    3. Value pattern analysis
    4. Data distribution analysis
    """
    
    # HTYPE Registry: code -> (name, formula_set, keywords, is_pii, sensitivity)
    HTYPE_REGISTRY: Dict[str, Dict[str, Any]] = {
        # PART B — PERSONAL & IDENTITY DATA
        "HTYPE-001": {
            "name": "Full Name",
            "formula_set": "FNAME",
            "keywords": ["full_name", "fullname", "name", "student_name", "patient_name", 
                        "employee_name", "customer_name", "client_name", "person_name",
                        "applicant_name", "candidate_name", "member_name"],
            "exclude_keywords": ["first_name", "last_name", "middle_name", "fname", "lname",
                                "product_name", "item_name", "company_name", "file_name",
                                "org_name", "organization_name", "column_name", "table_name"],
            "is_pii": True,
            "sensitivity": "medium"
        },
        "HTYPE-002": {
            "name": "First/Last/Middle Name",
            "formula_set": "SNAME",
            "keywords": ["first_name", "fname", "firstname", "given_name", "last_name", 
                        "lname", "lastname", "surname", "family_name", "middle_name",
                        "middlename", "mname", "maiden_name"],
            "is_pii": True,
            "sensitivity": "medium"
        },
        "HTYPE-003": {
            "name": "Unique ID / Record ID",
            "formula_set": "UID",
            "keywords": ["id", "student_id", "record_id", "emp_id", "employee_id",
                        "case_no", "case_id", "patient_id", "user_id", "customer_id",
                        "order_id", "transaction_id", "record_no", "registration_no",
                        "roll_no", "roll_number", "admission_no", "account_id",
                        "member_id", "client_id", "applicant_id"],
            "exclude_keywords": ["national_id", "passport", "ssn", "pan", "citizenship"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-007": {
            "name": "Age",
            "formula_set": "AGE",
            "keywords": ["age", "patient_age", "years", "age_years", "age_in_years",
                        "current_age", "employee_age", "student_age"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-008": {
            "name": "Gender / Sex",
            "formula_set": "GEN",
            "keywords": ["gender", "sex", "male_female", "m_f"],
            "is_pii": True,
            "sensitivity": "medium"
        },
        "HTYPE-029": {
            "name": "National ID / Passport / Government ID",
            "formula_set": "GOVID",
            "keywords": ["passport_no", "passport_number", "passport", "national_id",
                        "pan_number", "pan", "ssn", "social_security", "citizenship_no",
                        "citizenship", "drivers_license", "license_no", "voter_id",
                        "aadhaar", "nid", "national_identity"],
            "is_pii": True,
            "sensitivity": "high"
        },
        "HTYPE-030": {
            "name": "Blood Group",
            "formula_set": "BLOOD",
            "keywords": ["blood_group", "blood_type", "bloodgroup", "bloodtype",
                        "rh_factor", "blood"],
            "is_pii": True,
            "sensitivity": "medium"
        },
        "HTYPE-038": {
            "name": "Language / Nationality / Ethnicity",
            "formula_set": "CULT",
            "keywords": ["language", "nationality", "ethnicity", "mother_tongue",
                        "native_language", "ethnic_group", "race", "country_of_origin"],
            "is_pii": True,
            "sensitivity": "high"
        },
        "HTYPE-039": {
            "name": "Education Level / Qualification",
            "formula_set": "EDU",
            "keywords": ["qualification", "education", "degree", "education_level",
                        "highest_education", "educational_qualification", "academic_level",
                        "school_level", "grade_level"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-040": {
            "name": "Marital Status",
            "formula_set": "MAR",
            "keywords": ["marital_status", "civil_status", "relationship_status",
                        "married", "marriage_status"],
            "is_pii": True,
            "sensitivity": "medium"
        },
        
        # PART C — DATE & TIME DATA
        "HTYPE-004": {
            "name": "Date",
            "formula_set": "DATE",
            "keywords": ["date", "dob", "date_of_birth", "birth_date", "birthdate",
                        "admission_date", "joining_date", "event_date", "start_date",
                        "end_date", "due_date", "expiry_date", "hire_date", "order_date",
                        "purchase_date", "registration_date", "created_date", "updated_date",
                        "appointment_date", "visit_date", "discharge_date", "delivery_date"],
            "exclude_keywords": ["datetime", "timestamp", "created_at", "updated_at"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-005": {
            "name": "Time",
            "formula_set": "TIME",
            "keywords": ["time", "check_in", "check_out", "appointment_time", "start_time",
                        "end_time", "arrival_time", "departure_time", "clock_in", "clock_out",
                        "login_time", "logout_time"],
            "exclude_keywords": ["datetime", "timestamp"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-006": {
            "name": "DateTime (Combined)",
            "formula_set": "DTM",
            "keywords": ["created_at", "updated_at", "timestamp", "submitted_on",
                        "recorded_datetime", "datetime", "logged_at", "modified_at",
                        "deleted_at", "last_login", "last_accessed", "event_datetime"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-033": {
            "name": "Duration / Time Elapsed",
            "formula_set": "DUR",
            "keywords": ["duration", "tenure", "years_of_service", "session_length",
                        "time_elapsed", "time_spent", "length", "period", "service_years",
                        "experience", "work_experience"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-041": {
            "name": "Fiscal Period / Academic Year",
            "formula_set": "FISC",
            "keywords": ["fiscal_year", "fy", "academic_year", "quarter", "semester",
                        "term", "financial_year", "reporting_period", "ay", "batch",
                        "session", "school_year"],
            "is_pii": False,
            "sensitivity": "low"
        },
        
        # PART D — CONTACT & LOCATION DATA
        "HTYPE-009": {
            "name": "Phone / Mobile Number",
            "formula_set": "PHONE",
            "keywords": ["phone", "mobile", "contact", "tel", "cell", "phone_number",
                        "mobile_number", "contact_number", "telephone", "cell_phone",
                        "home_phone", "work_phone", "office_phone", "emergency_contact",
                        "whatsapp", "fax"],
            "is_pii": True,
            "sensitivity": "medium"
        },
        "HTYPE-010": {
            "name": "Email Address",
            "formula_set": "EMAIL",
            "keywords": ["email", "email_address", "mail", "e_mail", "emailid",
                        "email_id", "work_email", "personal_email", "contact_email"],
            "is_pii": True,
            "sensitivity": "medium"
        },
        "HTYPE-011": {
            "name": "Address / Location (Full)",
            "formula_set": "ADDR",
            "keywords": ["address", "full_address", "residential_address", "street_address",
                        "home_address", "office_address", "mailing_address", "permanent_address",
                        "temporary_address", "current_address", "location", "addr"],
            "exclude_keywords": ["email_address", "ip_address", "web_address"],
            "is_pii": True,
            "sensitivity": "high"
        },
        "HTYPE-012": {
            "name": "City / District / Region",
            "formula_set": "CITY",
            "keywords": ["city", "district", "region", "province", "state", "municipality",
                        "town", "county", "locality", "area", "zone", "suburb"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-013": {
            "name": "Country",
            "formula_set": "CNTRY",
            "keywords": ["country", "nationality_country", "country_code", "country_name",
                        "nation", "origin_country", "destination_country"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-014": {
            "name": "Postal Code / ZIP Code",
            "formula_set": "POST",
            "keywords": ["zip", "postal_code", "postcode", "pin_code", "zipcode",
                        "zip_code", "pincode", "postal"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-035": {
            "name": "Coordinates (Latitude / Longitude)",
            "formula_set": "GEO",
            "keywords": ["latitude", "longitude", "lat", "lng", "lon", "coordinates",
                        "geo_location", "gps", "lat_long", "geolocation"],
            "is_pii": False,
            "sensitivity": "low"
        },
        
        # PART E — NUMERIC & FINANCIAL DATA
        "HTYPE-015": {
            "name": "Numeric Amount / Currency / Revenue",
            "formula_set": "AMT",
            "keywords": ["amount", "revenue", "price", "salary", "cost", "fee", "budget",
                        "income", "expense", "payment", "total_amount", "net_amount",
                        "gross_amount", "balance", "credit", "debit", "invoice_amount",
                        "transaction_amount", "unit_price", "selling_price", "purchase_price",
                        "discount", "tax", "vat", "wages", "bonus", "commission"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-016": {
            "name": "Quantity / Count / Integer Metric",
            "formula_set": "QTY",
            "keywords": ["count", "qty", "quantity", "units", "no_of_students", "total",
                        "number_of", "num", "items", "pieces", "stock", "inventory",
                        "headcount", "enrollment", "attendance", "frequency"],
            "exclude_keywords": ["account_number", "phone_number", "roll_number"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-017": {
            "name": "Percentage / Rate / Ratio",
            "formula_set": "PCT",
            "keywords": ["rate", "percent", "percentage", "pass_rate", "growth", "ratio",
                        "conversion_rate", "success_rate", "failure_rate", "attendance_rate",
                        "completion_rate", "interest_rate", "tax_rate", "pct"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-021": {
            "name": "Score / Rating / Grade / GPA",
            "formula_set": "SCORE",
            "keywords": ["score", "grade", "marks", "rating", "gpa", "cgpa", "points",
                        "result", "final_grade", "exam_score", "test_score", "assessment",
                        "performance", "evaluation", "star_rating", "review_score"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-042": {
            "name": "Currency Code",
            "formula_set": "CUR",
            "keywords": ["currency", "currency_code", "currency_type", "curr",
                        "money_type", "payment_currency"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-043": {
            "name": "Rank / Ordinal",
            "formula_set": "RANK",
            "keywords": ["rank", "position_rank", "standing", "place", "order",
                        "ranking", "leaderboard_position", "class_rank"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-044": {
            "name": "Calculated / Derived Column",
            "formula_set": "CALC",
            "keywords": ["total", "net", "gross", "profit", "loss", "balance",
                        "difference", "sum", "subtotal", "grand_total", "net_total",
                        "calculated", "derived", "computed"],
            "is_pii": False,
            "sensitivity": "low"
        },
        
        # PART F — CLASSIFICATION & STATUS DATA
        "HTYPE-018": {
            "name": "Boolean / Flag / Yes-No Field",
            "formula_set": "BOOL",
            "keywords": ["is_active", "flag", "verified", "approved", "has_submitted",
                        "is_valid", "is_enabled", "is_deleted", "active", "enabled",
                        "disabled", "confirmed", "is_", "has_", "can_"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-019": {
            "name": "Category / Classification Label",
            "formula_set": "CAT",
            "keywords": ["category", "type", "class", "segment", "group", "stream",
                        "classification", "section", "tier", "level", "division",
                        "branch", "faculty", "subject_type"],
            "exclude_keywords": ["blood_type", "currency_type"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-020": {
            "name": "Status Field",
            "formula_set": "STAT",
            "keywords": ["status", "stage", "condition", "progress", "state",
                        "workflow_status", "order_status", "payment_status",
                        "application_status", "approval_status", "process_status"],
            "exclude_keywords": ["marital_status", "civil_status"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-045": {
            "name": "Survey / Likert Response",
            "formula_set": "SURV",
            "keywords": ["response", "satisfaction", "agree_disagree", "survey_q",
                        "likert", "feedback_score", "nps", "csat", "rating_response",
                        "q1", "q2", "q3", "question_"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-046": {
            "name": "Multi-Value / Tag Field",
            "formula_set": "MULTI",
            "keywords": ["subjects", "tags", "skills", "interests", "activities",
                        "hobbies", "languages_spoken", "certifications", "keywords",
                        "labels", "categories", "topics"],
            "is_pii": False,
            "sensitivity": "low"
        },
        
        # PART G — ORGANIZATIONAL & PRODUCT DATA
        "HTYPE-024": {
            "name": "Product Name / Item Name",
            "formula_set": "PROD",
            "keywords": ["product", "item", "medicine", "service_name", "item_name",
                        "product_name", "good", "merchandise", "article", "drug_name",
                        "medication"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-025": {
            "name": "Product Code / SKU / Barcode",
            "formula_set": "SKU",
            "keywords": ["sku", "barcode", "product_code", "item_code", "upc",
                        "ean", "gtin", "article_number", "part_number", "model_number"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-026": {
            "name": "Organization / Company Name",
            "formula_set": "ORG",
            "keywords": ["company", "organization", "employer", "school_name",
                        "institution", "org_name", "business_name", "firm",
                        "vendor", "supplier", "client_company", "partner"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-027": {
            "name": "Job Title / Designation / Role",
            "formula_set": "JOB",
            "keywords": ["designation", "job_title", "position", "role", "post",
                        "occupation", "profession", "title", "job_role"],
            "exclude_keywords": ["product_title", "movie_title", "book_title"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-028": {
            "name": "Department / Division / Unit",
            "formula_set": "DEPT",
            "keywords": ["department", "dept", "division", "unit", "ward", "section",
                        "team", "branch", "wing", "bureau"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-034": {
            "name": "Serial Number / Reference Number",
            "formula_set": "REFNO",
            "keywords": ["serial_no", "invoice_no", "receipt_no", "ref_code",
                        "tracking_no", "reference_number", "voucher_no", "bill_no",
                        "ticket_no", "confirmation_number", "booking_ref", "order_ref"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-047": {
            "name": "Version / Revision Number",
            "formula_set": "VER",
            "keywords": ["version", "revision", "release", "ver", "rev",
                        "version_number", "build", "edition"],
            "is_pii": False,
            "sensitivity": "low"
        },
        
        # PART H — MEDICAL DATA
        "HTYPE-031": {
            "name": "Diagnosis / Medical Condition",
            "formula_set": "DIAG",
            "keywords": ["diagnosis", "condition", "icd_code", "illness", "disease",
                        "medical_condition", "health_condition", "disorder",
                        "ailment", "prognosis"],
            "is_pii": True,
            "sensitivity": "high"
        },
        "HTYPE-032": {
            "name": "Weight / Height / Physical Measurement",
            "formula_set": "PHYS",
            "keywords": ["weight", "height", "bmi", "temperature", "bp", "pulse",
                        "blood_pressure", "heart_rate", "body_mass", "waist",
                        "chest", "vital_signs"],
            "is_pii": True,
            "sensitivity": "medium"
        },
        
        # PART I — TEXT & TECHNICAL DATA
        "HTYPE-022": {
            "name": "Text / Notes / Description",
            "formula_set": "TEXT",
            "keywords": ["notes", "remarks", "description", "comments", "feedback",
                        "reason", "observation", "summary", "narrative", "details",
                        "explanation", "message", "text", "content", "bio"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-023": {
            "name": "URL / Website",
            "formula_set": "URL",
            "keywords": ["url", "website", "link", "profile_url", "source",
                        "web_address", "homepage", "webpage", "site", "href"],
            "is_pii": False,
            "sensitivity": "low"
        },
        "HTYPE-036": {
            "name": "IP Address",
            "formula_set": "IP",
            "keywords": ["ip_address", "ip", "user_ip", "client_ip", "server_ip",
                        "source_ip", "destination_ip", "ipv4", "ipv6"],
            "is_pii": True,
            "sensitivity": "medium"
        },
        "HTYPE-037": {
            "name": "File Name / File Path",
            "formula_set": "FILE",
            "keywords": ["file", "filename", "file_name", "document_path", "attachment",
                        "file_path", "document", "filepath", "upload", "download"],
            "is_pii": False,
            "sensitivity": "low"
        },
    }
    
    # Value patterns for secondary detection (when column name doesn't match)
    VALUE_PATTERNS = {
        "HTYPE-010": {  # Email
            "pattern": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "min_match_ratio": 0.5
        },
        "HTYPE-009": {  # Phone
            "pattern": r'^[\+]?[\d\s\-\(\)]{7,20}$',
            "min_match_ratio": 0.5
        },
        "HTYPE-023": {  # URL
            "pattern": r'^(https?://|www\.)[^\s]+',
            "min_match_ratio": 0.5
        },
        "HTYPE-036": {  # IP Address
            "pattern": r'^(\d{1,3}\.){3}\d{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$',
            "min_match_ratio": 0.5
        },
        "HTYPE-035": {  # Coordinates
            "pattern": r'^-?\d{1,3}\.\d+$',  # Decimal degree format
            "min_match_ratio": 0.7
        },
        "HTYPE-008": {  # Gender
            "pattern": r'^(male|female|m|f|man|woman|boy|girl|other|non-binary|transgender|prefer not to say)$',
            "min_match_ratio": 0.7,
            "case_insensitive": True
        },
        "HTYPE-030": {  # Blood Group
            "pattern": r'^(A|B|AB|O)[+-]?$|^(A|B|AB|O)\s*(positive|negative|pos|neg)$',
            "min_match_ratio": 0.7,
            "case_insensitive": True
        },
        "HTYPE-018": {  # Boolean
            "pattern": r'^(yes|no|y|n|true|false|1|0|on|off|active|inactive)$',
            "min_match_ratio": 0.8,
            "case_insensitive": True
        },
        "HTYPE-042": {  # Currency Code
            "pattern": r'^[A-Z]{3}$',  # ISO 4217
            "min_match_ratio": 0.8
        },
    }
    
    # Date patterns for HTYPE-004 detection
    DATE_PATTERNS = [
        r'^\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}$',  # Various date formats
        r'^\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4}$',
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{2,4}$',
    ]
    
    # DateTime patterns for HTYPE-006 detection
    DATETIME_PATTERNS = [
        r'^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(:\d{2})?',
        r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s+\d{1,2}:\d{2}',
    ]
    
    # Time patterns for HTYPE-005 detection
    TIME_PATTERNS = [
        r'^\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm)?$',
        r'^\d{1,2}\s*(AM|PM|am|pm)$',
    ]

    def __init__(self):
        """Initialize the HTYPE detector."""
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Build reverse index from keywords to HTYPE codes for fast lookup."""
        self._keyword_to_htype: Dict[str, List[str]] = {}
        self._exact_match_keywords: Dict[str, str] = {}
        
        for htype_code, config in self.HTYPE_REGISTRY.items():
            for keyword in config["keywords"]:
                keyword_lower = keyword.lower()
                # Exact matches for common keywords
                if keyword_lower not in self._exact_match_keywords:
                    self._exact_match_keywords[keyword_lower] = htype_code
                # Partial match index
                if keyword_lower not in self._keyword_to_htype:
                    self._keyword_to_htype[keyword_lower] = []
                self._keyword_to_htype[keyword_lower].append(htype_code)
    
    def _normalize_column_name(self, col: str) -> str:
        """Normalize column name for matching."""
        # Convert to lowercase, replace common separators with underscore
        normalized = col.lower().strip()
        normalized = re.sub(r'[\s\-\.]+', '_', normalized)
        normalized = re.sub(r'[^a-z0-9_]', '', normalized)
        return normalized
    
    def _get_exclude_keywords(self, htype_code: str) -> List[str]:
        """Get exclusion keywords for an HTYPE."""
        config = self.HTYPE_REGISTRY.get(htype_code, {})
        return [k.lower() for k in config.get("exclude_keywords", [])]
    
    def _check_exclusions(self, col_normalized: str, htype_code: str) -> bool:
        """Check if column matches any exclusion keywords for this HTYPE."""
        exclude_keywords = self._get_exclude_keywords(htype_code)
        for excl in exclude_keywords:
            if excl in col_normalized:
                return True
        return False
    
    def _match_by_column_name(self, col: str) -> Optional[Tuple[str, float, str]]:
        """
        Match HTYPE by column name.
        Returns: (htype_code, confidence, match_reason) or None
        """
        col_normalized = self._normalize_column_name(col)
        
        # Priority 1: Exact match
        if col_normalized in self._exact_match_keywords:
            htype_code = self._exact_match_keywords[col_normalized]
            if not self._check_exclusions(col_normalized, htype_code):
                return (htype_code, 1.0, f"Exact column name match: '{col}'")
        
        # Priority 2: Partial keyword match (check if any keyword is contained in column name)
        best_match: Optional[Tuple[str, float, str]] = None
        best_keyword_len = 0
        
        for keyword, htype_codes in self._keyword_to_htype.items():
            if keyword in col_normalized:
                # Check if this is a better match (longer keyword = more specific)
                if len(keyword) > best_keyword_len:
                    for htype_code in htype_codes:
                        if not self._check_exclusions(col_normalized, htype_code):
                            best_match = (htype_code, 0.85, f"Keyword '{keyword}' found in column name")
                            best_keyword_len = len(keyword)
                            break
        
        if best_match:
            return best_match
        
        # Priority 3: Check if column name contains any keyword
        for htype_code, config in self.HTYPE_REGISTRY.items():
            for keyword in config["keywords"]:
                keyword_lower = keyword.lower()
                # Check for prefix matches (e.g., "is_" prefix for boolean)
                if keyword_lower.endswith("_") and col_normalized.startswith(keyword_lower):
                    if not self._check_exclusions(col_normalized, htype_code):
                        return (htype_code, 0.75, f"Prefix pattern '{keyword_lower}' matched")
        
        return None
    
    def _match_by_value_pattern(self, col: str, series: pd.Series) -> Optional[Tuple[str, float, str]]:
        """
        Match HTYPE by analyzing value patterns.
        Returns: (htype_code, confidence, match_reason) or None
        """
        # Get non-null sample values
        non_null = series.dropna().astype(str)
        if len(non_null) == 0:
            return None
        
        sample_size = min(100, len(non_null))
        sample = non_null.sample(n=sample_size, random_state=42) if len(non_null) > sample_size else non_null
        
        # Check each value pattern
        for htype_code, pattern_config in self.VALUE_PATTERNS.items():
            pattern = pattern_config["pattern"]
            min_ratio = pattern_config.get("min_match_ratio", 0.5)
            case_insensitive = pattern_config.get("case_insensitive", False)
            
            flags = re.IGNORECASE if case_insensitive else 0
            regex = re.compile(pattern, flags)
            
            matches = sum(1 for v in sample if regex.match(str(v).strip()))
            match_ratio = matches / len(sample)
            
            if match_ratio >= min_ratio:
                confidence = 0.6 + (match_ratio - min_ratio) * 0.4  # Scale 0.6-1.0
                return (htype_code, confidence, f"Value pattern match ({match_ratio:.0%} of values)")
        
        # Check date/time patterns
        date_match = self._check_temporal_patterns(sample)
        if date_match:
            return date_match
        
        return None
    
    def _check_temporal_patterns(self, sample: pd.Series) -> Optional[Tuple[str, float, str]]:
        """Check for date/time patterns in values."""
        # Check DateTime first (more specific)
        datetime_matches = 0
        for pattern in self.DATETIME_PATTERNS:
            regex = re.compile(pattern, re.IGNORECASE)
            datetime_matches += sum(1 for v in sample if regex.match(str(v).strip()))
        
        if datetime_matches / len(sample) >= 0.5:
            return ("HTYPE-006", 0.7, "DateTime value pattern detected")
        
        # Check Time-only
        time_matches = 0
        for pattern in self.TIME_PATTERNS:
            regex = re.compile(pattern, re.IGNORECASE)
            time_matches += sum(1 for v in sample if regex.match(str(v).strip()))
        
        if time_matches / len(sample) >= 0.5:
            return ("HTYPE-005", 0.7, "Time value pattern detected")
        
        # Check Date-only
        date_matches = 0
        for pattern in self.DATE_PATTERNS:
            regex = re.compile(pattern, re.IGNORECASE)
            date_matches += sum(1 for v in sample if regex.match(str(v).strip()))
        
        if date_matches / len(sample) >= 0.5:
            return ("HTYPE-004", 0.7, "Date value pattern detected")
        
        return None
    
    def _match_by_distribution(self, col: str, series: pd.Series) -> Optional[Tuple[str, float, str]]:
        """
        Match HTYPE by analyzing data distribution.
        Returns: (htype_code, confidence, match_reason) or None
        """
        non_null = series.dropna()
        if len(non_null) == 0:
            return None
        
        # Check for numeric-only columns
        numeric_series = pd.to_numeric(non_null, errors='coerce')
        numeric_ratio = numeric_series.notna().sum() / len(non_null)
        
        if numeric_ratio >= 0.9:
            # It's numeric - determine which numeric HTYPE
            numeric_values = numeric_series.dropna()
            
            if len(numeric_values) == 0:
                return None
            
            min_val = numeric_values.min()
            max_val = numeric_values.max()
            mean_val = numeric_values.mean()
            
            # Check for Age (0-120 range, integers mostly)
            col_lower = col.lower()
            if min_val >= 0 and max_val <= 150:
                decimal_ratio = (numeric_values != numeric_values.astype(int)).sum() / len(numeric_values)
                if decimal_ratio < 0.1:  # Mostly integers
                    if "age" in col_lower or "years" in col_lower:
                        return ("HTYPE-007", 0.6, "Numeric distribution suggests age (0-120 integer range)")
            
            # Check for Percentage (0-100 or 0-1 range)
            if (min_val >= 0 and max_val <= 100) or (min_val >= 0 and max_val <= 1):
                if "percent" in col_lower or "rate" in col_lower or "ratio" in col_lower:
                    return ("HTYPE-017", 0.6, "Numeric distribution suggests percentage")
            
            # Check for Score/Rating (limited range, often 0-10, 0-100, 0-5, 1-5)
            unique_count = numeric_values.nunique()
            if unique_count <= 11 and min_val >= 0 and max_val <= 10:
                return ("HTYPE-021", 0.5, "Limited numeric range suggests score/rating")
            
            # Check for Rank (positive integers, sequential-like)
            if min_val >= 1 and max_val <= len(non_null) * 2:
                decimal_ratio = (numeric_values != numeric_values.astype(int)).sum() / len(numeric_values)
                if decimal_ratio < 0.05:
                    return ("HTYPE-043", 0.4, "Positive integer range suggests rank")
            
            # Default to Quantity for general positive integers
            if min_val >= 0:
                decimal_ratio = (numeric_values != numeric_values.astype(int)).sum() / len(numeric_values)
                if decimal_ratio < 0.1:
                    return ("HTYPE-016", 0.4, "General positive integer distribution")
            
            # Default to Amount for numeric with decimals
            return ("HTYPE-015", 0.35, "General numeric distribution with decimals")
        
        # Check for low-cardinality text columns (likely Category or Status)
        if series.dtype == object or str(series.dtype).startswith('str'):
            unique_count = non_null.nunique()
            unique_ratio = unique_count / len(non_null)
            
            if unique_count <= 10 and unique_ratio < 0.1:
                # Low cardinality - likely categorical
                col_lower = col.lower()
                if "status" in col_lower or "state" in col_lower:
                    return ("HTYPE-020", 0.5, "Low cardinality suggests status field")
                return ("HTYPE-019", 0.45, "Low cardinality suggests category field")
            
            # High cardinality text - likely free text or names
            avg_length = non_null.astype(str).str.len().mean()
            if avg_length > 50:
                return ("HTYPE-022", 0.4, "High average text length suggests free text/notes")
        
        return None
    
    def detect_column_htype(self, col: str, series: pd.Series) -> HtypeMatch:
        """
        Detect the HTYPE for a single column.
        
        Args:
            col: Column name
            series: Column data as pandas Series
            
        Returns:
            HtypeMatch with detection results
        """
        # Try matching in priority order
        
        # 1. Column name match (highest priority)
        name_match = self._match_by_column_name(col)
        if name_match and name_match[1] >= 0.75:
            htype_code, confidence, reason = name_match
            config = self.HTYPE_REGISTRY[htype_code]
            return HtypeMatch(
                htype_code=htype_code,
                htype_name=config["name"],
                formula_set=config["formula_set"],
                confidence=confidence,
                match_reason=reason,
                is_pii=config["is_pii"],
                sensitivity_level=config["sensitivity"]
            )
        
        # 2. Value pattern match
        pattern_match = self._match_by_value_pattern(col, series)
        if pattern_match and pattern_match[1] >= 0.6:
            htype_code, confidence, reason = pattern_match
            config = self.HTYPE_REGISTRY[htype_code]
            return HtypeMatch(
                htype_code=htype_code,
                htype_name=config["name"],
                formula_set=config["formula_set"],
                confidence=confidence,
                match_reason=reason,
                is_pii=config["is_pii"],
                sensitivity_level=config["sensitivity"]
            )
        
        # 3. Distribution analysis
        dist_match = self._match_by_distribution(col, series)
        if dist_match:
            htype_code, confidence, reason = dist_match
            config = self.HTYPE_REGISTRY[htype_code]
            return HtypeMatch(
                htype_code=htype_code,
                htype_name=config["name"],
                formula_set=config["formula_set"],
                confidence=confidence,
                match_reason=reason,
                is_pii=config["is_pii"],
                sensitivity_level=config["sensitivity"]
            )
        
        # 4. Fallback: use lower-confidence name match if available
        if name_match:
            htype_code, confidence, reason = name_match
            config = self.HTYPE_REGISTRY[htype_code]
            return HtypeMatch(
                htype_code=htype_code,
                htype_name=config["name"],
                formula_set=config["formula_set"],
                confidence=confidence,
                match_reason=reason,
                is_pii=config["is_pii"],
                sensitivity_level=config["sensitivity"]
            )
        
        # 5. Default to Text/Notes for unmatched columns
        return HtypeMatch(
            htype_code="HTYPE-022",
            htype_name="Text / Notes / Description",
            formula_set="TEXT",
            confidence=0.2,
            match_reason="No specific type detected, defaulting to text",
            is_pii=False,
            sensitivity_level="low"
        )
    
    def detect_all_columns(self, df: pd.DataFrame) -> Dict[str, HtypeMatch]:
        """
        Detect HTYPEs for all columns in a DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dict mapping column names to HtypeMatch objects
        """
        results: Dict[str, HtypeMatch] = {}
        
        for col in df.columns:
            results[col] = self.detect_column_htype(col, df[col])
        
        return results
    
    def get_htype_map(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Get simplified HTYPE map for storage in database.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dict mapping column names to HTYPE codes
        """
        detections = self.detect_all_columns(df)
        return {col: match.htype_code for col, match in detections.items()}
    
    def get_pii_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Identify columns that contain PII data.
        
        Args:
            df: Input DataFrame
            
        Returns:
            List of column names classified as PII
        """
        detections = self.detect_all_columns(df)
        return [col for col, match in detections.items() if match.is_pii]
    
    def get_high_sensitivity_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Identify columns with high sensitivity level.
        
        Args:
            df: Input DataFrame
            
        Returns:
            List of column names with high sensitivity
        """
        detections = self.detect_all_columns(df)
        return [col for col, match in detections.items() if match.sensitivity_level == "high"]
    
    def get_detection_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a comprehensive HTYPE detection report.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dict with full detection details and summary statistics
        """
        detections = self.detect_all_columns(df)
        
        # Group columns by HTYPE
        by_htype: Dict[str, List[str]] = {}
        for col, match in detections.items():
            if match.htype_code not in by_htype:
                by_htype[match.htype_code] = []
            by_htype[match.htype_code].append(col)
        
        # Count by formula set
        by_formula_set: Dict[str, int] = {}
        for match in detections.values():
            by_formula_set[match.formula_set] = by_formula_set.get(match.formula_set, 0) + 1
        
        # Calculate confidence statistics
        confidences = [match.confidence for match in detections.values()]
        
        return {
            "column_count": len(df.columns),
            "detections": {col: {
                "htype_code": match.htype_code,
                "htype_name": match.htype_name,
                "formula_set": match.formula_set,
                "confidence": match.confidence,
                "match_reason": match.match_reason,
                "is_pii": match.is_pii,
                "sensitivity_level": match.sensitivity_level
            } for col, match in detections.items()},
            "htype_map": {col: match.htype_code for col, match in detections.items()},
            "columns_by_htype": by_htype,
            "columns_by_formula_set": by_formula_set,
            "pii_columns": [col for col, match in detections.items() if match.is_pii],
            "high_sensitivity_columns": [col for col, match in detections.items() 
                                         if match.sensitivity_level == "high"],
            "confidence_stats": {
                "min": min(confidences) if confidences else 0,
                "max": max(confidences) if confidences else 0,
                "mean": sum(confidences) / len(confidences) if confidences else 0,
                "low_confidence_count": sum(1 for c in confidences if c < 0.5)
            }
        }


# Convenience function for direct usage
def detect_htypes(df: pd.DataFrame) -> Dict[str, str]:
    """
    Convenience function to detect HTYPEs for all columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dict mapping column names to HTYPE codes
    """
    detector = HtypeDetector()
    return detector.get_htype_map(df)
