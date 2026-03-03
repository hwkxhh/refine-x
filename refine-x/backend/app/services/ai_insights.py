"""
AI Insight Generator — Stage 5: Pre-computation before GPT.
Uses GPT-4o to generate natural language insights for charts,
with Python-computed statistics passed to GPT for explanation only.
"""

import json
import re
from typing import Any

import numpy as np
import pandas as pd
from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _parse_json(text: str):
    clean = re.sub(r"```[a-z]*\n?", "", text).strip()
    return json.loads(clean)


def _confidence_category(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _precompute_statistics(chart_data: list[dict], x_header: str) -> dict:
    """
    Stage 5 Pre-computation: Compute all statistics in Python BEFORE calling GPT.
    
    Computes:
    - peaks: Maximum values and their x-axis positions
    - lows: Minimum values and their x-axis positions  
    - trends: Direction (increasing/decreasing/stable), slope, R² if applicable
    - outliers: Values beyond 1.5 IQR
    - anomalies: Sudden jumps or drops (>2 std deviations from rolling mean)
    - period_comparisons: First half vs second half comparison
    - averages: Mean, median, mode
    """
    df = pd.DataFrame(chart_data)
    
    if "y" not in df.columns or len(df) == 0:
        return {"error": "No y-axis data available"}
    
    # Convert to numeric
    y_values = pd.to_numeric(df["y"], errors="coerce")
    x_values = df.get("x", pd.Series(range(len(df))))
    
    # Filter out NaN
    valid_mask = ~y_values.isna()
    y_clean = y_values[valid_mask].reset_index(drop=True)
    x_clean = x_values[valid_mask].reset_index(drop=True)
    
    if len(y_clean) == 0:
        return {"error": "No valid numeric y-axis data"}
    
    stats = {}
    
    # ===== PEAKS =====
    max_val = float(y_clean.max())
    max_idx = int(y_clean.idxmax())
    stats["peaks"] = {
        "maximum_value": round(max_val, 4),
        "maximum_at": str(x_clean.iloc[max_idx]) if max_idx < len(x_clean) else "N/A",
        "maximum_index": max_idx,
    }
    
    # ===== LOWS =====
    min_val = float(y_clean.min())
    min_idx = int(y_clean.idxmin())
    stats["lows"] = {
        "minimum_value": round(min_val, 4),
        "minimum_at": str(x_clean.iloc[min_idx]) if min_idx < len(x_clean) else "N/A",
        "minimum_index": min_idx,
    }
    
    # ===== AVERAGES =====
    stats["averages"] = {
        "mean": round(float(y_clean.mean()), 4),
        "median": round(float(y_clean.median()), 4),
        "std_dev": round(float(y_clean.std()), 4) if len(y_clean) > 1 else 0,
        "total": round(float(y_clean.sum()), 4),
        "count": len(y_clean),
    }
    
    # ===== TRENDS =====
    if len(y_clean) >= 3:
        try:
            # Linear regression for trend
            x_numeric = np.arange(len(y_clean))
            slope, intercept = np.polyfit(x_numeric, y_clean.values, 1)
            
            # Calculate R² 
            y_pred = slope * x_numeric + intercept
            ss_res = np.sum((y_clean.values - y_pred) ** 2)
            ss_tot = np.sum((y_clean.values - y_clean.mean()) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Determine direction
            if abs(slope) < 0.01 * stats["averages"]["mean"]:
                direction = "stable"
            elif slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"
            
            # Calculate percentage change from first to last
            first_val = y_clean.iloc[0]
            last_val = y_clean.iloc[-1]
            pct_change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
            
            stats["trends"] = {
                "direction": direction,
                "slope": round(float(slope), 6),
                "r_squared": round(float(r_squared), 4),
                "overall_change_percent": round(float(pct_change), 2),
                "confidence": "high" if r_squared > 0.7 else ("medium" if r_squared > 0.4 else "low"),
            }
        except Exception:
            stats["trends"] = {"direction": "unknown", "error": "Could not compute trend"}
    else:
        stats["trends"] = {"direction": "insufficient_data", "note": "Need at least 3 data points"}
    
    # ===== OUTLIERS (IQR method) =====
    if len(y_clean) >= 4:
        q1 = y_clean.quantile(0.25)
        q3 = y_clean.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outlier_mask = (y_clean < lower_bound) | (y_clean > upper_bound)
        outlier_indices = y_clean[outlier_mask].index.tolist()
        
        outliers = []
        for idx in outlier_indices[:5]:  # Limit to 5
            outliers.append({
                "x": str(x_clean.iloc[idx]) if idx < len(x_clean) else "N/A",
                "y": round(float(y_clean.iloc[idx]), 4),
                "index": idx,
            })
        
        stats["outliers"] = {
            "count": len(outlier_indices),
            "iqr_lower_bound": round(float(lower_bound), 4),
            "iqr_upper_bound": round(float(upper_bound), 4),
            "outlier_points": outliers,
        }
    else:
        stats["outliers"] = {"count": 0, "note": "Need at least 4 data points for IQR"}
    
    # ===== ANOMALIES (sudden jumps/drops) =====
    if len(y_clean) >= 5:
        # Rolling mean with window of 3
        rolling_mean = y_clean.rolling(window=3, center=True).mean()
        rolling_std = y_clean.rolling(window=3, center=True).std()
        
        # Find points that deviate more than 2 std from rolling mean
        anomalies = []
        for i in range(len(y_clean)):
            if pd.notna(rolling_mean.iloc[i]) and pd.notna(rolling_std.iloc[i]):
                if rolling_std.iloc[i] > 0:
                    z_score = abs(y_clean.iloc[i] - rolling_mean.iloc[i]) / rolling_std.iloc[i]
                    if z_score > 2:
                        anomalies.append({
                            "x": str(x_clean.iloc[i]) if i < len(x_clean) else "N/A",
                            "y": round(float(y_clean.iloc[i]), 4),
                            "z_score": round(float(z_score), 2),
                            "index": i,
                        })
        
        stats["anomalies"] = {
            "count": len(anomalies),
            "anomaly_points": anomalies[:5],  # Limit to 5
        }
    else:
        stats["anomalies"] = {"count": 0, "note": "Need at least 5 data points"}
    
    # ===== PERIOD COMPARISONS (first half vs second half) =====
    if len(y_clean) >= 4:
        mid = len(y_clean) // 2
        first_half = y_clean.iloc[:mid]
        second_half = y_clean.iloc[mid:]
        
        first_avg = first_half.mean()
        second_avg = second_half.mean()
        change_pct = ((second_avg - first_avg) / first_avg * 100) if first_avg != 0 else 0
        
        stats["period_comparisons"] = {
            "first_half_average": round(float(first_avg), 4),
            "second_half_average": round(float(second_avg), 4),
            "change_percent": round(float(change_pct), 2),
            "first_half_total": round(float(first_half.sum()), 4),
            "second_half_total": round(float(second_half.sum()), 4),
        }
    else:
        stats["period_comparisons"] = {"note": "Need at least 4 data points"}
    
    # ===== COMPARISON TO AVERAGE =====
    stats["comparison_to_average"] = {
        "above_average_count": int((y_clean > stats["averages"]["mean"]).sum()),
        "below_average_count": int((y_clean < stats["averages"]["mean"]).sum()),
        "at_average_count": int((y_clean == stats["averages"]["mean"]).sum()),
    }
    
    return stats


def generate_chart_insight(
    chart_type: str,
    x_header: str,
    y_header: str | None,
    chart_data: list[dict],
    user_goal: str,
) -> dict:
    """
    Stage 5: Generate insight with pre-computation.
    
    1. Python computes all statistics (peaks, lows, trends, outliers, anomalies)
    2. Pre-computed findings passed to GPT
    3. GPT writes explanations ONLY — never invents statistics
    
    Returns:
    {
        "insight": str,
        "confidence_score": float,
        "confidence": str,
        "recommendations": [{"action": str, "reasoning": str}],
        "computed_statistics": dict  # The pre-computed stats
    }
    """
    # ===== STAGE 5: PRE-COMPUTATION =====
    precomputed = _precompute_statistics(chart_data, x_header)
    
    y_label = y_header or "count"
    precomputed_json = json.dumps(precomputed, indent=2, default=str)

    prompt = f"""You are writing insights for a {chart_type} chart.
X-axis: "{x_header}", Y-axis: "{y_label}"
User's analytical goal: "{user_goal}"

IMPORTANT: The following statistics have been PRE-COMPUTED by Python. 
You MUST use these exact numbers — do not invent or calculate any statistics yourself.

PRE-COMPUTED STATISTICS:
{precomputed_json}

Your task:
1. Write a natural language analysis explaining these pre-computed findings
2. Relate the findings to the user's goal
3. Provide 2-3 actionable recommendations based on the data

Rules:
- ONLY reference numbers that appear in the pre-computed statistics above
- NEVER invent statistics or calculations
- Use the exact values provided (peaks, lows, trends, outliers, etc.)
- Set confidence_score based on the trend r_squared and data quality

Return ONLY valid JSON:
{{
  "insight": "Natural language explanation of the pre-computed statistics...",
  "confidence_score": 0.85,
  "recommendations": [
    {{"action": "Specific action to take", "reasoning": "Based on the computed statistics"}}
  ]
}}"""

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1200,
    )

    result = _parse_json(response.choices[0].message.content)
    score = float(result.get("confidence_score", 0.5))
    result["confidence"] = _confidence_category(score)
    result["confidence_score"] = round(score, 3)
    
    # Include the pre-computed statistics in the response
    result["computed_statistics"] = precomputed
    
    return result


def _generate_fallback_insight(
    chart_type: str,
    x_header: str,
    y_header: str | None,
    chart_data: list[dict],
    user_goal: str,
) -> dict:
    """
    Fully deterministic insight generation — no GPT required.
    Uses _precompute_statistics() to derive natural language findings.
    """
    stats = _precompute_statistics(chart_data, x_header)
    y_label = y_header or "count"

    if "error" in stats:
        insight = (
            f"This {chart_type} chart displays {x_header} on the X-axis and {y_label} on the Y-axis. "
            f"Insufficient numeric data was available to compute detailed statistics."
        )
        return {
            "insight": insight,
            "confidence": "low",
            "confidence_score": 0.2,
            "recommendations": [],
        }

    parts = []
    recs = []

    avg = stats["averages"]
    peaks = stats["peaks"]
    lows = stats["lows"]
    n = avg["count"]

    # Opening sentence
    parts.append(
        f"This {chart_type} chart compares {x_header} (X-axis) against {y_label} (Y-axis) "
        f"across {n} data point{'s' if n != 1 else ''}."
    )

    # Peak & low
    parts.append(
        f"The highest value is {peaks['maximum_value']:,} at '{peaks['maximum_at']}', "
        f"while the lowest is {lows['minimum_value']:,} at '{lows['minimum_at']}'. "
        f"The mean is {avg['mean']:,} with a total of {avg['total']:,}."
    )

    # Trend
    trend = stats.get("trends", {})
    direction = trend.get("direction", "unknown")
    if direction in ("increasing", "decreasing"):
        pct = trend.get("overall_change_percent", 0)
        parts.append(
            f"Overall, {y_label} shows a {direction} trend with a {abs(pct):.1f}% "
            f"{'increase' if pct >= 0 else 'decrease'} from first to last point "
            f"(R\u00b2 = {trend.get('r_squared', 0):.2f})."
        )
        recs.append({
            "action": f"Investigate what drives the {direction} trend in {y_label}",
            "reasoning": f"A {abs(pct):.1f}% change was detected across the dataset.",
        })
    elif direction == "stable":
        parts.append(f"{y_label} remains relatively stable across all {x_header} values.")

    # Period comparison
    period = stats.get("period_comparisons", {})
    if "change_percent" in period:
        cp = period["change_percent"]
        if abs(cp) >= 5:
            half_dir = "improved" if cp > 0 else "declined"
            parts.append(
                f"Comparing first half to second half, performance {half_dir} by {abs(cp):.1f}% "
                f"(avg {period['first_half_average']:,} \u2192 {period['second_half_average']:,})."
            )

    # Outliers
    outliers = stats.get("outliers", {})
    if outliers.get("count", 0) > 0:
        pts = outliers["outlier_points"]
        labels = ", ".join(f"'{p['x']}' ({p['y']:,})" for p in pts[:3])
        parts.append(f"{outliers['count']} outlier{'s' if outliers['count'] != 1 else ''} detected: {labels}.")
        recs.append({
            "action": f"Review the outlier{'s' if outliers['count'] != 1 else ''} in {x_header}",
            "reasoning": f"Values at {labels} fall outside the expected IQR range.",
        })

    # Goal alignment
    if user_goal and user_goal.lower() not in ("general data analysis", "general analysis", ""):
        recs.append({
            "action": f"Align findings with your goal: {user_goal}",
            "reasoning": "Focus on the peak and trend values most relevant to this objective.",
        })

    # Confidence from trend quality or data size
    r2 = trend.get("r_squared", 0) if direction not in ("unknown", "insufficient_data") else 0
    score = max(0.35, min(0.85, 0.4 + r2 * 0.4 + min(n, 20) * 0.01))

    return {
        "insight": " ".join(parts),
        "confidence": _confidence_category(score),
        "confidence_score": round(score, 3),
        "recommendations": recs[:3],
    }


def generate_comparison_insight(deltas: list[dict], significant: list[dict]) -> str:
    """Generate a plain-text AI insight explaining comparison deltas."""
    delta_text = json.dumps(deltas[:20], default=str, indent=2)
    sig_text = json.dumps(significant, default=str, indent=2)

    prompt = f"""You are comparing two datasets from different time periods.

All changes (% delta per column):
{delta_text}

Significant changes (>20%):
{sig_text}

In 3-4 sentences, explain:
1. What are the top changes?
2. What might have caused them?
3. What should the user pay attention to?

Be specific and concise."""

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=400,
    )

    return response.choices[0].message.content.strip()
