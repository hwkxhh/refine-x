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
from app.services.chart_type_rules import precompute_chart_types

_client = OpenAI(api_key=settings.OPENAI_API_KEY)
import logging
logger = logging.getLogger(__name__)


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

    logger.info(
        f"[GPT CALL START] classify_and_assign — file={filename!r}  "
        f"columns={len(columns)}  {columns}"
    )

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=3000,
        )
        logger.info(
            f"[GPT CALL SUCCESS] classify_and_assign — file={filename!r}  "
            f"tokens used: {response.usage.total_tokens}"
        )
    except Exception as e:
        logger.error(
            f"[GPT CALL FAILED] classify_and_assign — file={filename!r}  "
            f"{type(e).__name__}: {e}"
        )
        raise

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


# ============================================================================
# VISUALIZATION & ANALYSIS SUGGESTIONS — used by /formula-suggestions route
# ============================================================================

def _build_suggestions_deterministically(columns: list[str], df) -> dict:
    """
    Fallback: generate suggested_analyses and recommended_visualizations
    from column types without calling GPT.  Produces 10-12 analyses with
    dataset-specific 'why' text and smart 'auto_select' (top 5 only).
    """
    import pandas as pd

    lower_cols = {c: c.lower().replace("_", " ").replace("-", " ") for c in columns}

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = [c for c in df.select_dtypes(include=["object", "category"]).columns.tolist()
                if df[c].nunique() <= 30]
    date_cols = [c for c in columns if any(k in lower_cols[c] for k in ["date", "time", "year", "month", "period"])]

    # Semantic helpers — find columns by keyword
    def _find(keywords, pool=None):
        pool = pool or columns
        for c in pool:
            for k in keywords:
                if k in lower_cols.get(c, c.lower()):
                    return c
        return None

    amt_col   = _find(["amount", "revenue", "sales", "total"], numeric_cols)
    profit_col = _find(["profit", "margin", "income", "earnings"], numeric_cols)
    qty_col   = _find(["quantity", "qty", "count", "units"], numeric_cols)
    cat_col   = _find(["category", "type", "class", "segment"])
    subcat_col = _find(["sub-category", "sub_category", "subcategory", "sub category"])
    payment_col = _find(["payment", "pay mode", "paymentmode", "pay_mode", "method"])
    state_col = _find(["state", "region", "province"])
    city_col  = _find(["city", "district", "area"])
    name_col  = _find(["customer", "client", "name"])
    date_col  = date_cols[0] if date_cols else None

    analyses = []
    vizzes = []
    auto_slots = 5  # how many to auto-select
    rank = 0        # tracks importance ordering

    def _add(name, desc, why, cols, ftype, example, viz=None):
        nonlocal rank
        analyses.append({
            "name": name, "description": desc, "why": why,
            "columns_needed": [c for c in cols if c],
            "formula_type": ftype, "example": example,
            "auto_select": rank < auto_slots,
        })
        if viz:
            vizzes.append(viz)
        rank += 1

    # --- 1. Revenue / Amount Trend Over Time ---
    if date_col and amt_col:
        _add(
            "Revenue Trend Over Time",
            f"Track how {amt_col} changes over {date_col}",
            f"Your dataset has {amt_col} and {date_col} — a time-series line chart will reveal whether revenue is growing, flat, or declining month over month.",
            [date_col, amt_col], "time_series",
            f"Is {amt_col} growing or declining over time?",
            {"chart_type": "line", "x_column": date_col, "y_column": amt_col,
             "reason": f"Line chart tracking {amt_col} over {date_col}"},
        )

    # --- 2. Profit by Category ---
    if cat_col and profit_col:
        _add(
            "Profit by Category",
            f"Compare {profit_col} across {cat_col} groups",
            f"With {cat_col} and {profit_col} columns present, a grouped bar chart will show which product categories are actually profitable vs. which are dragging margins down.",
            [cat_col, profit_col], "aggregation",
            f"Which {cat_col} generates the most {profit_col}?",
            {"chart_type": "bar", "x_column": cat_col, "y_column": profit_col,
             "reason": f"Bar chart of {profit_col} by {cat_col}"},
        )
    elif cat_col and amt_col:
        _add(
            "Category Performance",
            f"Compare {amt_col} across {cat_col} groups",
            f"Your {cat_col} column lets you see which groups drive the most {amt_col} — essential for prioritisation.",
            [cat_col, amt_col], "aggregation",
            f"Which {cat_col} has the highest {amt_col}?",
            {"chart_type": "bar", "x_column": cat_col, "y_column": amt_col,
             "reason": f"Bar chart of {amt_col} by {cat_col}"},
        )

    # --- 3. Profit Margin Analysis (derived metric) ---
    if amt_col and profit_col:
        _add(
            "Profit Margin Analysis",
            f"Calculate {profit_col} ÷ {amt_col} to find true margins",
            f"Dividing {profit_col} by {amt_col} produces a margin percentage — this reveals which orders or categories have high revenue but razor-thin margins, the most actionable metric in the dataset.",
            [amt_col, profit_col], "comparison",
            f"Which rows have the worst margins?",
            {"chart_type": "scatter", "x_column": amt_col, "y_column": profit_col,
             "reason": f"Scatter of {amt_col} vs {profit_col} to spot margin outliers"},
        )

    # --- 4. Geographic Analysis ---
    geo_col = state_col or city_col
    metric_col = amt_col or (numeric_cols[0] if numeric_cols else None)
    if geo_col and metric_col:
        _add(
            "Geographic Analysis",
            f"Compare {metric_col} across {geo_col}",
            f"The {geo_col} column enables regional performance comparison — you can identify under-performing regions or high-potential markets.",
            [geo_col, metric_col], "aggregation",
            f"Which {geo_col} has the highest {metric_col}?",
            {"chart_type": "bar", "x_column": geo_col, "y_column": metric_col,
             "reason": f"Bar chart of {metric_col} by {geo_col}"},
        )

    # --- 5. Customer Analysis ---
    if name_col and metric_col:
        _add(
            "Customer Analysis",
            f"Rank customers by {metric_col}",
            f"Your {name_col} column lets you identify the top-spending customers and spot concentration risk — if 20% of customers drive 80% of revenue, that's a risk signal.",
            [name_col, metric_col], "aggregation",
            f"Who are the top 10 customers by {metric_col}?",
        )

    # --- 6. Profit Trend Over Time ---
    if date_col and profit_col:
        _add(
            "Profit Trend Over Time",
            f"Track how {profit_col} changes over {date_col}",
            f"Revenue can grow while profit shrinks. Tracking {profit_col} over {date_col} separately reveals margin compression that a combined chart hides.",
            [date_col, profit_col], "time_series",
            f"Is {profit_col} growing in line with revenue?",
            {"chart_type": "line", "x_column": date_col, "y_column": profit_col,
             "reason": f"Line chart tracking {profit_col} over {date_col}"},
        )

    # --- 7. Revenue vs Profit Combined ---
    if date_col and amt_col and profit_col:
        _add(
            "Revenue vs Profit Combined",
            f"Overlay {amt_col} and {profit_col} trends on one chart",
            f"Putting both {amt_col} and {profit_col} on the same timeline reveals whether profit keeps pace with revenue or if costs are eating into margins.",
            [date_col, amt_col, profit_col], "time_series",
            f"Are revenue and profit growing at the same rate?",
        )

    # --- 8. Sub-Category Deep Dive ---
    if subcat_col and metric_col:
        _add(
            "Sub-Category Deep Dive",
            f"Granular {metric_col} breakdown by {subcat_col}",
            f"The {subcat_col} column gives you a more granular view than {cat_col or 'category'} — you can pinpoint exactly which product lines perform best or worst.",
            [subcat_col, metric_col], "aggregation",
            f"Which {subcat_col} drives the most {metric_col}?",
            {"chart_type": "bar", "x_column": subcat_col, "y_column": metric_col,
             "reason": f"Bar chart of {metric_col} by {subcat_col}"},
        )

    # --- 9. Payment Mode Analysis ---
    if payment_col and metric_col:
        _add(
            "Payment Mode Analysis",
            f"Compare {metric_col} across {payment_col}",
            f"Your {payment_col} column reveals operational insights — do certain payment methods correlate with higher order values or lower margins?",
            [payment_col, metric_col], "aggregation",
            f"Which {payment_col} has the highest average {metric_col}?",
            {"chart_type": "pie", "x_column": payment_col, "y_column": metric_col,
             "reason": f"Pie chart showing {metric_col} distribution by {payment_col}"},
        )

    # --- 10. Quantity vs Profit ---
    if qty_col and profit_col:
        _add(
            "Quantity vs Profit",
            f"Check if higher {qty_col} means higher {profit_col}",
            f"Having both {qty_col} and {profit_col} lets you test whether volume equals profitability — some high-volume products may actually lose money.",
            [qty_col, profit_col], "correlation",
            f"Does selling more units always mean more profit?",
            {"chart_type": "scatter", "x_column": qty_col, "y_column": profit_col,
             "reason": f"Scatter plot of {qty_col} vs {profit_col}"},
        )

    # --- 11. Monthly Order Volume ---
    if date_col:
        _add(
            "Monthly Order Volume",
            f"Count orders per month using {date_col}",
            f"Counting rows by {date_col} shows operational throughput — are you processing more or fewer orders over time?",
            [date_col], "time_series",
            f"How many orders per month?",
        )

    # --- 12. Loss-Making Products ---
    if profit_col and (subcat_col or cat_col):
        group_col = subcat_col or cat_col
        _add(
            "Loss-Making Products",
            f"Identify {group_col} groups with negative {profit_col}",
            f"Filtering {group_col} by negative {profit_col} is a critical risk flag — these are products or categories actively losing money.",
            [group_col, profit_col], "comparison",
            f"Which {group_col} have total negative {profit_col}?",
        )

    # --- Catch-all: correlation from any two numeric cols ---
    if len(numeric_cols) >= 2 and rank < 10:
        a, b = numeric_cols[0], numeric_cols[1]
        _add(
            "Correlation Analysis",
            f"Explore relationships between {a} and {b}",
            f"Your dataset has multiple numeric columns ({a}, {b}) — a scatter plot will reveal whether they move together, inversely, or independently.",
            [a, b], "correlation",
            f"Does {a} increase when {b} increases?",
            {"chart_type": "scatter", "x_column": a, "y_column": b,
             "reason": f"Scatter plot of {a} vs {b}"},
        )

    # --- Catch-all: category distribution ---
    if cat_cols and rank < 12:
        c = cat_cols[0]
        _add(
            "Category Distribution",
            f"Show the proportion of each {c} group",
            f"A pie chart of {c} shows how balanced or skewed the dataset is across groups.",
            [c], "distribution",
            f"What percentage does each {c} represent?",
            {"chart_type": "pie", "x_column": c,
             "y_column": numeric_cols[0] if numeric_cols else c,
             "reason": f"Pie chart of {c} distribution"},
        )

    # --- Absolute fallback ---
    if not analyses:
        first_col = columns[0] if columns else "column"
        second_col = columns[1] if len(columns) > 1 else first_col
        analyses.append({
            "name": "Summary Statistics",
            "description": "Compute summary statistics across all columns",
            "why": f"With {len(columns)} columns in the dataset, a statistical summary is the essential first step to understand ranges and outliers.",
            "columns_needed": columns[:2],
            "formula_type": "summary",
            "example": "Mean, median, min, max for all numeric columns",
            "auto_select": True,
        })
        vizzes.append({
            "chart_type": "bar",
            "x_column": first_col,
            "y_column": second_col,
            "reason": f"Bar chart comparing {first_col} and {second_col}",
        })

    # Remove any viz where x and y are the same column
    vizzes = [v for v in vizzes if v.get("x_column") != v.get("y_column")]
    # Apply chart-type rulebook to every viz for analyst-grade type selection
    vizzes = precompute_chart_types(vizzes, df)
    return {"suggested_analyses": analyses, "recommended_visualizations": vizzes}


def suggest_analyses_and_viz(
    columns: list[str],
    sample_rows: list[dict],
    filename: str,
    df=None,
) -> dict:
    """
    Generate suggested_analyses and recommended_visualizations for the
    formula-suggestions endpoint. Tries GPT first, falls back to deterministic.
    """
    sample_text = json.dumps(sample_rows[:5], default=str, indent=2)
    columns_text = ", ".join(f'"{ c}"' for c in columns)

    # Pre-compute rulebook chart type hints for GPT
    rulebook_hint = ""
    if df is not None:
        from app.services.chart_type_rules import determine_chart_type as _rule_fn
        import pandas as _pd
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        date_cols = [c for c in columns if any(k in str(c).lower() for k in ["date", "time", "year", "month"])]
        hints = []
        for dc in date_cols[:1]:
            for nc in numeric_cols[:3]:
                r = _rule_fn(dc, nc, df)
                hints.append(f"  {dc} vs {nc} → {r['chart_type']} ({r['reason'][:80]})")
        for nc1 in numeric_cols[:2]:
            for nc2 in numeric_cols[:2]:
                if nc1 != nc2:
                    r = _rule_fn(nc1, nc2, df)
                    hints.append(f"  {nc1} vs {nc2} → {r['chart_type']} ({r['reason'][:80]})")
        if hints:
            rulebook_hint = "\n\nPre-computed chart type suggestions (from analyst rulebook):\n" + "\n".join(hints[:8])
            rulebook_hint += "\nUse these chart types unless you have a specific reason to override."

    prompt = f"""You are a data analytics advisor. Given a dataset, suggest 10-12 analyses and 5-8 chart recommendations.

File: "{filename}"
Columns: [{columns_text}]
Sample data (first 5 rows):
{sample_text}{rulebook_hint}

Return ONLY this JSON (no other text):
{{
  "suggested_analyses": [
    {{
      "name": "Short analysis name",
      "description": "One sentence describing the analysis",
      "why": "Explain specifically WHY this dataset needs this analysis — reference actual column names and what the user will learn. NOT a template.",
      "columns_needed": ["col1", "col2"],
      "formula_type": "correlation|aggregation|distribution|time_series|comparison",
      "example": "Example question this answers",
      "auto_select": true
    }}
  ],
  "recommended_visualizations": [
    {{
      "chart_type": "bar|horizontal_bar|line|scatter|pie|donut|stacked_bar|area",
      "x_column": "exact_column_name",
      "y_column": "exact_column_name",
      "reason": "Why this chart is useful",
      "group_by": null
    }}
  ]
}}

CRITICAL RULES:
- Suggest 10-12 distinct analyses that cover every useful angle of this dataset
- "why" must be specific to THIS file — mention actual column names, what patterns
  the user might find, and what business question it answers. Never use template text.
- Set "auto_select": true for the 5 most important analyses only. The rest are false.
- The 5 auto-selected should always be the highest-value insights for this data domain.
- x_column and y_column MUST be exact column names from the list above
- Chart type rules: date+numeric=line, category(<=7)+numeric=bar, category(>7)+numeric=horizontal_bar,
  two numerics=scatter, few categories proportion=donut, time+category+numeric=stacked_bar
- Include time-series analyses if any date/time column exists
- Include derived-metric analyses (e.g., profit margin = profit/amount)
- Include geographic analyses if location columns exist
- Include customer/entity analyses if name columns exist
- For pie/donut charts, x_column = category column, y_column = numeric column
- For line charts, x_column should be a date/time or sequential column"""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=3000,
        )
        result = _parse_json_from_response(response.choices[0].message.content)
        if result.get("suggested_analyses") or result.get("recommended_visualizations"):
            # Ensure every analysis has why + auto_select fields
            auto_count = 0
            for a in result.get("suggested_analyses", []):
                a.setdefault("why", a.get("description", ""))
                a.setdefault("auto_select", False)
                if a["auto_select"]:
                    auto_count += 1
            # If GPT selected too many or none, fix it
            if auto_count == 0 or auto_count > 5:
                for i, a in enumerate(result.get("suggested_analyses", [])):
                    a["auto_select"] = i < 5
            # Run chart-type rulebook on recommended visualisations
            if df is not None and result.get("recommended_visualizations"):
                result["recommended_visualizations"] = precompute_chart_types(
                    result["recommended_visualizations"], df
                )
            return result
    except Exception:
        pass

    # Fallback to deterministic logic
    if df is not None:
        return _build_suggestions_deterministically(columns, df)

    # Last resort: minimal fallback
    return {
        "suggested_analyses": [
            {
                "name": "Summary Statistics",
                "description": "Overview of key statistics across all columns",
                "why": f"Your file '{filename}' has {len(columns)} columns — a summary will show the range, average, and outliers across all numeric fields.",
                "columns_needed": columns[:2],
                "formula_type": "summary",
                "example": "Mean, median and distribution of numeric columns",
                "auto_select": True,
            }
        ],
        "recommended_visualizations": [
            {
                "chart_type": "bar",
                "x_column": columns[0] if columns else "",
                "y_column": columns[1] if len(columns) > 1 else columns[0] if columns else "",
                "reason": "Initial overview of the dataset",
            }
        ],
    }


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
