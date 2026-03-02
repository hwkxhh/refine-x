"""
AI Analysis Service — uses OpenAI GPT-4o to:
  classify_and_assign() — Single GPT call returns HTYPE + Formulas (Stage 1+2)

Logic First. AI Never. — GPT only classifies; all cleaning is deterministic.
"""

import json
import re
from typing import Optional

from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


# ============================================================================
# CORRECT HTYPE REGISTRY (from htype_detector.py)
# ============================================================================
# This MUST match the HTYPE_REGISTRY in app/services/htype_detector.py exactly

HTYPE_REGISTRY = {
    # PART B — PERSONAL & IDENTITY DATA
    "HTYPE-001": ("Full Name", "FNAME"),
    "HTYPE-002": ("First/Last/Middle Name", "SNAME"),
    "HTYPE-003": ("Unique ID / Record ID", "UID"),
    "HTYPE-007": ("Age", "AGE"),
    "HTYPE-008": ("Gender / Sex", "GEN"),
    "HTYPE-029": ("National ID / Passport / Government ID", "GOVID"),
    "HTYPE-030": ("Blood Group", "BLOOD"),
    "HTYPE-038": ("Language / Nationality / Ethnicity", "CULT"),
    "HTYPE-039": ("Education Level / Qualification", "EDU"),
    "HTYPE-040": ("Marital Status", "MAR"),
    
    # PART C — DATE & TIME DATA
    "HTYPE-004": ("Date", "DATE"),
    "HTYPE-005": ("Time", "TIME"),
    "HTYPE-006": ("DateTime (Combined)", "DTM"),
    "HTYPE-033": ("Duration / Time Elapsed", "DUR"),
    "HTYPE-041": ("Fiscal Period / Academic Year", "FISC"),
    
    # PART D — CONTACT & LOCATION DATA
    "HTYPE-009": ("Phone / Mobile Number", "PHONE"),
    "HTYPE-010": ("Email Address", "EMAIL"),
    "HTYPE-011": ("Address / Location (Full)", "ADDR"),
    "HTYPE-012": ("City / District / Region", "CITY"),
    "HTYPE-013": ("Country", "CNTRY"),
    "HTYPE-014": ("Postal Code / ZIP Code", "POST"),
    "HTYPE-035": ("Coordinates (Latitude / Longitude)", "GEO"),
    
    # PART E — NUMERIC & FINANCIAL DATA
    "HTYPE-015": ("Numeric Amount / Currency / Revenue", "AMT"),
    "HTYPE-016": ("Quantity / Count / Integer Metric", "QTY"),
    "HTYPE-017": ("Percentage / Rate / Ratio", "PCT"),
    "HTYPE-021": ("Score / Rating / Grade / GPA", "SCORE"),
    "HTYPE-042": ("Currency Code", "CUR"),
    "HTYPE-043": ("Rank / Ordinal", "RANK"),
    "HTYPE-044": ("Calculated / Derived Column", "CALC"),
    
    # PART F — CLASSIFICATION & STATUS DATA
    "HTYPE-018": ("Boolean / Flag / Yes-No Field", "BOOL"),
    "HTYPE-019": ("Category / Classification Label", "CAT"),
    "HTYPE-020": ("Status Field", "STAT"),
    "HTYPE-045": ("Survey / Likert Response", "SURV"),
    "HTYPE-046": ("Multi-Value / Tag Field", "MULTI"),
    
    # PART G — ORGANIZATIONAL & PRODUCT DATA
    "HTYPE-024": ("Product Name / Item Name", "PROD"),
    "HTYPE-025": ("Product Code / SKU / Barcode", "SKU"),
    "HTYPE-026": ("Organization / Company Name", "ORG"),
    "HTYPE-027": ("Job Title / Designation / Role", "JOB"),
    "HTYPE-028": ("Department / Division / Unit", "DEPT"),
    "HTYPE-034": ("Serial Number / Reference Number", "REFNO"),
    "HTYPE-047": ("Version / Revision Number", "VER"),
    
    # PART H — MEDICAL DATA
    "HTYPE-031": ("Diagnosis / Medical Condition", "DIAG"),
    "HTYPE-032": ("Weight / Height / Physical Measurement", "PHYS"),
    
    # PART I — TEXT & TECHNICAL DATA
    "HTYPE-022": ("Text / Notes / Description", "TEXT"),
    "HTYPE-023": ("URL / Website", "URL"),
    "HTYPE-036": ("IP Address", "IP"),
    "HTYPE-037": ("File Name / File Path", "FILE"),
    
    # FALLBACK
    "HTYPE-000": ("Unclassified / Unknown", "FALLBACK"),
}

VALID_HTYPES = list(HTYPE_REGISTRY.keys())


# ============================================================================
# COMPLETE FORMULA REFERENCE BY HTYPE
# ============================================================================
FORMULA_REFERENCE = {
    "HTYPE-001": ["FNAME-01", "FNAME-02", "FNAME-03", "FNAME-04", "FNAME-05", "FNAME-06", "FNAME-07", "FNAME-08", "FNAME-09", "FNAME-10", "FNAME-11", "FNAME-14"],
    "HTYPE-002": ["SNAME-01", "SNAME-02", "SNAME-03", "SNAME-05", "SNAME-08"],
    "HTYPE-003": ["UID-01", "UID-02", "UID-03", "UID-05", "UID-08"],
    "HTYPE-007": ["AGE-01", "AGE-05", "AGE-10"],
    "HTYPE-008": ["GEN-01", "GEN-02"],
    "HTYPE-009": ["PHONE-01", "PHONE-02", "PHONE-03", "PHONE-05", "PHONE-07"],
    "HTYPE-010": ["EMAIL-01", "EMAIL-02", "EMAIL-03", "EMAIL-05", "EMAIL-07"],
    "HTYPE-015": ["AMT-01", "AMT-02", "AMT-03", "AMT-04", "AMT-05", "AMT-06", "AMT-07", "AMT-08", "AMT-09", "AMT-12", "AMT-13"],
    "HTYPE-016": ["QTY-01", "QTY-02", "QTY-03", "QTY-04", "QTY-05", "QTY-06", "QTY-07", "QTY-09"],
    "HTYPE-017": ["PCT-01", "PCT-02", "PCT-03"],
    "HTYPE-018": ["BOOL-01", "BOOL-02"],
    "HTYPE-019": ["CAT-01", "CAT-02", "CAT-03"],
    "HTYPE-020": ["STAT-01", "STAT-02"],
    "HTYPE-026": ["ORG-01", "ORG-02", "ORG-03", "ORG-04", "ORG-05"],
    "HTYPE-044": ["CALC-01", "CALC-02", "CALC-03", "CALC-05"],
    "HTYPE-000": ["FALLBACK-01", "FALLBACK-02"],
}


def _parse_json_from_response(text: str) -> dict | list:
    """Robustly extract JSON from GPT response even if it's wrapped in markdown."""
    # Strip markdown code fences
    clean = re.sub(r"```[a-z]*\n?", "", text).strip()
    return json.loads(clean)


def classify_and_assign(
    columns: list[str],
    sample_rows: list[dict],
    filename: str,
) -> dict:
    """
    COMBINED Stage 1 + Stage 2: Single GPT call returns both HTYPE classification
    AND formula assignments for every column.
    
    This replaces the separate analyze_headers() and suggest_formulas() calls,
    halving latency, halving cost, and ensuring consistency.
    
    Returns:
    {
        "columns": {
            "column_name": {
                "htype": "HTYPE-XXX",
                "confidence": 0.95,
                "formulas": ["SNAME-01", "SNAME-02", ...]
            }
        }
    }
    """
    sample_text = json.dumps(sample_rows[:5], default=str, indent=2)
    columns_text = ", ".join(f'"{c}"' for c in columns)
    
    # Build the complete HTYPE reference from the registry
    htype_reference_lines = []
    for code, (name, formula_set) in sorted(HTYPE_REGISTRY.items()):
        formulas = FORMULA_REFERENCE.get(code, ["FALLBACK-01", "FALLBACK-02"])
        htype_reference_lines.append(f"{code}: {name} → formulas: {formulas}")
    htype_reference = "\n".join(htype_reference_lines)

    prompt = f"""You are a data classification system. Analyze each column and:
1. Assign an HTYPE code with confidence score
2. Assign the corresponding formula list from the rulebook

File: "{filename}"
Columns: [{columns_text}]
Sample data (first 5 rows):
{sample_text}

COMPLETE HTYPE + FORMULA REFERENCE:
{htype_reference}

═══════════════════════════════════════════════════════════════════════════════
                        CRITICAL CLASSIFICATION GUIDELINES
═══════════════════════════════════════════════════════════════════════════════

CONTINUOUS MEASUREMENTS vs DISCRETE COUNTS:
  • HTYPE-016 (Quantity) is for DISCRETE COUNTABLE ITEMS:
    - "Order Count" (1, 2, 3 orders)
    - "Number of Students" (5, 10, 15)
    - "Items Sold" (3 items, 7 items)
    - ">16 Orders" or "16_orders" — how many orders above 16 (values: 0,1,2,3,4,5)
    - Column names starting with numeric thresholds (e.g., "16_orders") are COUNTS
  
  • HTYPE-015 (Amount) is for CONTINUOUS NUMERIC MEASUREMENTS:
    - "Sum of Distance" (12.5 km, 45.7 km) — DISTANCE IS A MEASUREMENT
    - "Total Earning" ($250.00, $1500.50)
    - "Revenue" (1000, 5000)
    - "Store Average" (4.2, 3.8)

  RULE: If you can say "how many X" → QTY. If you can say "how much X" → AMT.
  Distance is "how much" (12.5 km), not "how many" → AMT

CALCULATED/DERIVED COLUMNS:
  • HTYPE-044 (Calculated) is for columns DERIVED from other columns:
    - "Fuel" = Distance × 3 → CALC
    - "Avg. -2" or "avg_2" = Store Average minus 2 → CALC
    - "Net Total" = Payment - Deductions → CALC
    - "Total Earning" = Payment + Fuel → could be CALC if it's a sum of other columns
  
  RULE: If the column is mathematically derived from other columns, use CALC.

BOOLEAN vs QUANTITY TRAP:
  • HTYPE-018 (Boolean) is ONLY for true/false, yes/no, 0/1 binary values:
    - "MG Applicable" (Yes/No) → BOOL
    - "Is Active" (True/False) → BOOL
  
  • If values are 0, 1, 2, 3, 4, 5... → NOT Boolean, use HTYPE-016 (Quantity)
  • Column "16_orders" or ">16 Orders" with values 0,1,2,3,4,5 is HTYPE-016 (Quantity)

NAME COLUMNS:
  • "Rider First Name", "First Name", "fname" → HTYPE-002 (SNAME, not FNAME)
  • "Full Name", "Student Name", "Name" → HTYPE-001 (FNAME)

ORGANIZATION vs CATEGORY:
  • "Store Name", "Company", "Organization" → HTYPE-026 (ORG)
  • "Category", "Type", "Classification" → HTYPE-019 (CAT)

═══════════════════════════════════════════════════════════════════════════════

Return ONLY this exact JSON structure (no other text):
{{
  "columns": {{
    "column_name": {{
      "htype": "HTYPE-XXX",
      "confidence": 0.95,
      "formulas": ["FORMULA-01", "FORMULA-02"]
    }}
  }}
}}

Confidence: 0.9+ = certain, 0.7-0.9 = likely, 0.5-0.7 = uncertain, <0.5 = guess
Formulas: Use the COMPLETE formula list for the assigned HTYPE from the reference above."""

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=3000,
    )

    result = _parse_json_from_response(response.choices[0].message.content)
    
    # Validate structure and normalize
    if "columns" not in result:
        result = {"columns": result}
    
    # Ensure all columns are present with valid HTYPE and formulas
    for col in columns:
        if col not in result["columns"]:
            result["columns"][col] = {
                "htype": "HTYPE-000",
                "confidence": 0.0,
                "formulas": ["FALLBACK-01", "FALLBACK-02"]
            }
        else:
            entry = result["columns"][col]
            
            # Validate HTYPE
            if entry.get("htype") not in VALID_HTYPES:
                entry["htype"] = "HTYPE-000"
            
            # Normalize confidence
            entry["confidence"] = min(1.0, max(0.0, float(entry.get("confidence", 0.5))))
            
            # Ensure formulas list exists and uses correct formulas for HTYPE
            htype = entry["htype"]
            if "formulas" not in entry or not entry["formulas"]:
                entry["formulas"] = FORMULA_REFERENCE.get(htype, ["FALLBACK-01", "FALLBACK-02"])
    
    return result


# ============================================================================
# LEGACY FUNCTIONS — Deprecated, use classify_and_assign() instead
# ============================================================================

def analyze_headers(
    columns: list[str],
    sample_rows: list[dict],
    filename: str,
) -> dict:
    """
    DEPRECATED: Use classify_and_assign() instead.
    
    This function now wraps classify_and_assign() for backward compatibility.
    Returns only the HTYPE classification portion.
    """
    result = classify_and_assign(columns, sample_rows, filename)
    
    # Strip formulas to return legacy format
    legacy_result = {"columns": {}}
    for col, data in result["columns"].items():
        legacy_result["columns"][col] = {
            "htype": data["htype"],
            "confidence": data["confidence"]
        }
    
    return legacy_result


def suggest_formulas(
    columns: list[str],
    sample_rows: list[dict],
    filename: str,
    dataset_summary: Optional[str] = None,
    htype_map: Optional[dict] = None,
) -> dict:
    """
    DEPRECATED: Use classify_and_assign() instead.
    
    This function now wraps classify_and_assign() for backward compatibility.
    Returns only the formula assignment portion.
    """
    result = classify_and_assign(columns, sample_rows, filename)
    
    # Extract formulas to return legacy format
    legacy_result = {"instruction_set": {}}
    for col, data in result["columns"].items():
        legacy_result["instruction_set"][col] = data["formulas"]
    
    return legacy_result
