"""
AI Insight Generator — Stage 5: Pre-computation before GPT.
Uses GPT-4o to generate natural language insights for charts,
with Python-computed statistics passed to GPT for explanation only.
"""

import json
import logging
import re
from typing import Any

import numpy as np
import pandas as pd
from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)


def _parse_json(text: str):
    clean = re.sub(r"```[a-z]*\n?", "", text).strip()
    return json.loads(clean)


def _confidence_category(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def safe_precompute_statistics(
    chart_data: list[dict], x_col: str, y_col: str | None = None
) -> dict:
    """
    Compute statistics for any chart data safely.
    Handles any key naming convention (x/y, name/value, label/count, etc.).
    Never returns empty — always returns something meaningful.
    """
    effective_y = y_col or "value"
    stats: dict = {
        "x_column": x_col,
        "y_column": effective_y,
        "data_points": len(chart_data),
        "peaks": None,
        "lows": None,
        "averages": None,
        "trends": None,
        "outliers": None,
        "top_values": [],
        "bottom_values": [],
    }

    if not chart_data:
        stats["note"] = "No data available"
        return stats

    # ── Flexible value extraction ─────────────────────────────────────────
    # Try the explicit column name first, then common fallbacks
    y_candidates = [c for c in [y_col, "y", "value", "count", "amount", "total"] if c]
    x_candidates = [c for c in [x_col, "x", "name", "label", "category"] if c]

    y_values: list[float] = []
    x_labels: list[str] = []
    y_key_used: str | None = None

    for item in chart_data:
        y_val = None
        for key in y_candidates:
            if key in item and item[key] is not None:
                y_val = item[key]
                if y_key_used is None:
                    y_key_used = key
                break
        x_val = None
        for key in x_candidates:
            if key in item and item[key] is not None:
                x_val = item[key]
                break
        if y_val is not None:
            try:
                y_values.append(float(y_val))
                x_labels.append(str(x_val) if x_val is not None else f"item_{len(y_values)}")
            except (ValueError, TypeError):
                pass

    if not y_values:
        stats["note"] = "Could not extract numeric values from chart data"
        logger.warning(
            "[PRECOMPUTE] No numeric y-values found in chart_data. "
            f"Available keys: {list(chart_data[0].keys()) if chart_data else []}. "
            f"Tried y-candidates: {y_candidates}"
        )
        return stats

    if y_key_used:
        stats["y_key_used"] = y_key_used

    y_clean = pd.Series(y_values)
    x_clean = pd.Series(x_labels)

    try:
        # ── PEAKS & LOWS ──────────────────────────────────────────────────────
        max_idx = int(y_clean.idxmax())
        min_idx = int(y_clean.idxmin())
        stats["peaks"] = {
            "value": round(float(y_clean.max()), 4),
            "label": x_clean.iloc[max_idx] if max_idx < len(x_clean) else "unknown",
        }
        stats["lows"] = {
            "value": round(float(y_clean.min()), 4),
            "label": x_clean.iloc[min_idx] if min_idx < len(x_clean) else "unknown",
        }

        # ── AVERAGES ──────────────────────────────────────────────────────────
        stats["averages"] = {
            "mean": round(float(y_clean.mean()), 4),
            "median": round(float(y_clean.median()), 4),
            "std_dev": round(float(y_clean.std()), 4) if len(y_clean) > 1 else 0,
            "total": round(float(y_clean.sum()), 4),
            "count": len(y_clean),
        }

        # ── TOP / BOTTOM 3 ────────────────────────────────────────────────────
        sorted_pairs = sorted(zip(x_labels, y_values), key=lambda p: p[1], reverse=True)
        stats["top_values"] = [
            {"label": p[0], "value": round(p[1], 4)} for p in sorted_pairs[:3]
        ]
        stats["bottom_values"] = [
            {"label": p[0], "value": round(p[1], 4)} for p in sorted_pairs[-3:]
        ]

        # ── TRENDS (3+ data points) ───────────────────────────────────────────
        if len(y_values) >= 3:
            try:
                x_numeric = np.arange(len(y_values))
                slope, intercept = np.polyfit(x_numeric, y_values, 1)
                y_pred = slope * x_numeric + intercept
                ss_res = np.sum((np.array(y_values) - y_pred) ** 2)
                ss_tot = np.sum((np.array(y_values) - np.mean(y_values)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                mean_val = stats["averages"]["mean"]
                if abs(slope) < 0.01 * max(abs(mean_val), 1):
                    direction = "stable"
                elif slope > 0:
                    direction = "increasing"
                else:
                    direction = "decreasing"
                first_val = float(y_values[0])
                last_val = float(y_values[-1])
                pct_change = ((last_val - first_val) / max(abs(first_val), 1)) * 100
                stats["trends"] = {
                    "direction": direction,
                    "slope": round(float(slope), 6),
                    "r_squared": round(float(r_squared), 4),
                    "overall_change_percent": round(float(pct_change), 2),
                    "first_value": round(first_val, 4),
                    "last_value": round(last_val, 4),
                    "confidence": "high" if r_squared > 0.7 else ("medium" if r_squared > 0.4 else "low"),
                }
            except Exception as te:
                stats["trends"] = {"direction": "unknown", "error": str(te)}
        else:
            stats["trends"] = {"direction": "insufficient_data", "note": "Need at least 3 data points"}

        # ── OUTLIERS via IQR (5+ data points) ────────────────────────────────
        if len(y_values) >= 5:
            q1 = float(y_clean.quantile(0.25))
            q3 = float(y_clean.quantile(0.75))
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_pts = [
                {"label": x_labels[i], "value": round(v, 4)}
                for i, v in enumerate(y_values)
                if v < lower or v > upper
            ]
            stats["outliers"] = {
                "count": len(outlier_pts),
                "iqr_lower": round(lower, 4),
                "iqr_upper": round(upper, 4),
                "outlier_points": outlier_pts[:5],
            }
        else:
            stats["outliers"] = {"count": 0, "note": "Need at least 5 data points for IQR"}

        # ── PERIOD COMPARISONS (4+ data points) ──────────────────────────────
        if len(y_values) >= 4:
            mid = len(y_values) // 2
            first_half = y_clean.iloc[:mid]
            second_half = y_clean.iloc[mid:]
            first_avg = float(first_half.mean())
            second_avg = float(second_half.mean())
            cp = ((second_avg - first_avg) / max(abs(first_avg), 1)) * 100
            stats["period_comparisons"] = {
                "first_half_average": round(first_avg, 4),
                "second_half_average": round(second_avg, 4),
                "change_percent": round(float(cp), 2),
                "first_half_total": round(float(first_half.sum()), 4),
                "second_half_total": round(float(second_half.sum()), 4),
            }

        # ── COMPARISON TO AVERAGE ─────────────────────────────────────────────
        stats["comparison_to_average"] = {
            "above_average_count": int((y_clean > stats["averages"]["mean"]).sum()),
            "below_average_count": int((y_clean < stats["averages"]["mean"]).sum()),
        }

    except Exception as e:
        logger.error(f"[PRECOMPUTE ERROR] {type(e).__name__}: {e}")
        stats["note"] = f"Partial statistics only — {type(e).__name__}"

    return stats


def build_insight_prompt(
    chart_title: str,
    chart_type: str,
    x_col: str,
    y_col: str,
    computed_stats: dict,
    dataset_domain: str,
    user_goal: str,
) -> str:
    """Build a specific, numbers-grounded prompt that prevents generic GPT output."""
    stats_json = json.dumps(computed_stats, indent=2, default=str)
    return f"""
You are a senior data analyst writing a specific, actionable insight for a business chart.

CHART INFORMATION:
- Title: {chart_title}
- Type: {chart_type}
- X-axis: {x_col}
- Y-axis: {y_col}
- Dataset domain: {dataset_domain or "general"}
- User's analysis goal: {user_goal or "General data exploration"}

COMPUTED STATISTICS (use ONLY these numbers — do not invent any):
{stats_json}

INSTRUCTIONS:
1. Write exactly 3 insight observations. Number them.
2. Every observation must reference a SPECIFIC number from the computed statistics above.
3. The first observation states the single most important finding.
4. The second observation provides context or comparison (e.g. above/below average, trend direction).
5. The third observation is a specific actionable recommendation based on the data.
6. Write in plain English. No jargon. No hedging phrases like "it appears" or "it seems".
7. Never say "this chart shows" or "this chart displays" — describe the data directly.
8. Every sentence must be specific to THIS data. Generic sentences that could apply to any chart are not acceptable.
9. If the computed statistics show a top performer, name it. If they show an outlier, name it. If they show a trend, state its direction and magnitude.

EXAMPLES OF BAD INSIGHTS (never write like this):
- "This bar chart displays category on the X-axis and amount on the Y-axis."
- "Insufficient numeric data was available to compute detailed statistics."
- "The data shows various trends across different categories."

EXAMPLES OF GOOD INSIGHTS (write like this):
- "Office Supplies leads with $2.09M in revenue, just 2.4% ahead of Electronics ($2.05M) and Furniture ($2.04M)."
- "Debit Card and Credit Card together account for 43.4% of orders, while COD represents the lowest share at 17.3%."
- "Binders have the lowest profit at $97,257 despite reasonable sales volume — consider optimising pricing or supplier costs."

Return ONLY valid JSON:
{{
  "insight": "1. [first observation]\\n\\n2. [second observation]\\n\\n3. [third observation]",
  "confidence_score": 0.85,
  "recommendations": [
    {{"action": "Specific action", "reasoning": "Based on a specific number from the stats"}}
  ]
}}"""


def generate_chart_insight(
    chart_type: str,
    x_header: str,
    y_header: str | None,
    chart_data: list[dict],
    user_goal: str,
    chart_title: str = "",
    dataset_domain: str = "",
) -> dict:
    """
    Stage 5: Generate GPT-backed insight with pre-computed statistics.

    1. Python computes all statistics (peaks, lows, trends, outliers, top/bottom values)
    2. Pre-computed findings + specific prompt sent to GPT
    3. GPT writes explanations ONLY — never invents statistics
    4. Exceptions are logged and re-raised so the caller can decide whether to fall back

    Returns:
    {
        "insight": str,
        "confidence_score": float,
        "confidence": str,
        "recommendations": [{"action": str, "reasoning": str}],
        "computed_statistics": dict
    }
    """
    chart_id_label = chart_title or f"{chart_type}/{x_header}"
    logger.info(f"[GPT CALL START] generate_chart_insight for chart '{chart_id_label}'")
    logger.info(f"[GPT INPUT] x_header={x_header!r}  y_header={y_header!r}  chart_type={chart_type!r}")
    logger.info(f"[GPT INPUT] data_points={len(chart_data)}  user_goal={user_goal!r}")

    # ── Pre-computation ───────────────────────────────────────────────────────
    precomputed = safe_precompute_statistics(chart_data, x_header, y_header)
    logger.info(f"[GPT INPUT] computed_stats keys: {[k for k, v in precomputed.items() if v is not None]}")

    y_label = y_header or "count"
    title = chart_title or f"{chart_type.replace('_', ' ').title()} of {y_label} by {x_header}"

    prompt = build_insight_prompt(
        chart_title=title,
        chart_type=chart_type,
        x_col=x_header,
        y_col=y_label,
        computed_stats=precomputed,
        dataset_domain=dataset_domain,
        user_goal=user_goal,
    )

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200,
        )
        logger.info(
            f"[GPT CALL SUCCESS] chart '{chart_id_label}' — "
            f"tokens used: {response.usage.total_tokens}"
        )
    except Exception as e:
        logger.error(
            f"[GPT CALL FAILED] chart '{chart_id_label}' — "
            f"{type(e).__name__}: {e}"
        )
        raise  # Re-raise so the route can decide whether to fall back

    result = _parse_json(response.choices[0].message.content)
    score = float(result.get("confidence_score", 0.5))
    result["confidence"] = _confidence_category(score)
    result["confidence_score"] = round(score, 3)
    result["computed_statistics"] = precomputed
    result["is_ai_generated"] = True
    result["model_name"] = "gpt-4o"

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
    stats = safe_precompute_statistics(chart_data, x_header, y_header)
    y_label = y_header or "count"

    if stats.get("averages") is None:
        # Pre-computation found no numeric data — return a minimal deterministic insight
        n = stats.get("data_points", 0)
        insight = (
            f"{n} data point{'s' if n != 1 else ''} are available for this {chart_type} chart "
            f"({x_header} vs {y_label}), but no numeric values could be extracted for analysis."
        )
        return {
            "insight": insight,
            "confidence": "low",
            "confidence_score": 0.2,
            "recommendations": [],
            "is_ai_generated": False,
            "model_name": "statistical_fallback",
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
        f"The highest value is {peaks['value']:,} at '{peaks['label']}', "
        f"while the lowest is {lows['value']:,} at '{lows['label']}'. "
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
        labels = ", ".join(f"'{p['label']}' ({p['value']:,})" for p in pts[:3])
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
        "is_ai_generated": False,
        "model_name": "statistical_fallback",
    }


def generate_comparison_insight(deltas: list[dict], significant: list[dict]) -> str:
    """Generate a plain-text AI insight explaining comparison deltas."""
    logger.info(
        f"[GPT CALL START] generate_comparison_insight — "
        f"total_deltas={len(deltas)}  significant_changes={len(significant)}"
    )
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

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=400,
        )
        logger.info(
            f"[GPT CALL SUCCESS] generate_comparison_insight — "
            f"tokens used: {response.usage.total_tokens}"
        )
    except Exception as e:
        logger.error(f"[GPT CALL FAILED] generate_comparison_insight — {type(e).__name__}: {e}")
        raise
    return response.choices[0].message.content.strip()


# ── Shared utilities used by fallback and async path ─────────────────────────

def _human_label(col_name: str) -> str:
    return col_name.replace("_", " ").replace("-", " ").title()


def _format_number(value) -> str:
    """Format a numeric value as a human-readable string (1.2M, 450K, etc.)."""
    try:
        v = float(value)
        if abs(v) >= 1_000_000_000:
            return f"{v / 1_000_000_000:.1f}B"
        if abs(v) >= 1_000_000:
            return f"{v / 1_000_000:.1f}M"
        if abs(v) >= 1_000:
            return f"{v / 1_000:.0f}K"
        return f"{v:.1f}"
    except Exception:
        return str(value)


def _generate_statistical_fallback(
    stats: dict, title: str, x_col: str, y_col: str
) -> str:
    """
    When GPT fails, produce a basic but honest insight from computed stats.
    Never returns the generic 'Insufficient data' message.
    Always references real numbers.
    """
    lines: list[str] = []

    peaks = stats.get("peaks") or {}
    lows = stats.get("lows") or {}
    averages = stats.get("averages") or {}
    trends = stats.get("trends") or {}

    if peaks.get("label"):
        lines.append(
            f"1. {peaks['label']} has the highest {_human_label(y_col)} "
            f"at {_format_number(peaks['value'])}."
        )

    if lows.get("label") and averages.get("mean") is not None:
        lines.append(
            f"2. {lows['label']} has the lowest value at {_format_number(lows['value'])}, "
            f"compared to the average of {_format_number(averages['mean'])}."
        )

    direction = trends.get("direction")
    if direction and direction not in ("unknown", "insufficient_data"):
        # key may be overall_change_percent (existing) or overall_change_pct (legacy)
        pct = trends.get("overall_change_percent", trends.get("overall_change_pct", 0))
        lines.append(
            f"3. The overall trend is {direction} "
            f"with a {abs(pct):.1f}% change from first to last period."
        )

    if not lines:
        top = stats.get("top_values", [])
        if len(top) > 0:
            lines.append(f"1. Top value: {top[0]['label']} at {_format_number(top[0]['value'])}.")
        if len(top) > 1:
            lines.append(f"2. Second: {top[1]['label']} at {_format_number(top[1]['value'])}.")
        if len(top) > 2:
            lines.append(f"3. Third: {top[2]['label']} at {_format_number(top[2]['value'])}.")

    if lines:
        return "\n".join(lines)
    return f"Data computed for {title}. {stats.get('data_points', 0)} data points analyzed."


async def generate_real_insight(
    chart_config: dict,
    chart_data: list,
    dataset_context: dict,
    openai_client,
) -> dict:
    """
    Async insight generator for any chart from any domain.
    Always calls GPT with real computed statistics.
    Falls back to _generate_statistical_fallback only if GPT throws.

    Args:
        chart_config:     {"x": col, "y": col, "type": chart_type, "title": str}
        chart_data:       list of dicts (Recharts-compatible payload)
        dataset_context:  {"domain", "total_rows", "filename", "goal"}
        openai_client:    An AsyncOpenAI instance (caller supplies it)

    Returns:
        {
            "insight":             str,
            "computed_statistics": dict,
            "model":               str,
            "tokens_used":         int | None,
            "is_ai_generated":     bool,
        }
    """
    x_col = chart_config.get("x", "")
    y_col = chart_config.get("y", "")
    chart_type = chart_config.get("type", "")
    chart_title = chart_config.get("title", "")

    # Step 1: Compute statistics — always produces something
    stats = safe_precompute_statistics(chart_data, x_col, y_col)

    # Step 2: Build context-aware prompt
    sample = chart_data[:5] + chart_data[-5:] if len(chart_data) > 10 else chart_data
    prompt = f"""You are a senior data analyst writing a specific, actionable insight.

DATASET CONTEXT:
- Domain: {dataset_context.get('domain', 'unknown')}
- Total rows: {dataset_context.get('total_rows', 'unknown')}
- File: {dataset_context.get('filename', 'unknown')}
- User goal: {dataset_context.get('goal', 'General analysis')}

CHART BEING ANALYZED:
- Title: {chart_title}
- Chart type: {chart_type}
- X axis: {x_col}
- Y axis: {y_col}

COMPUTED STATISTICS (reference these exact numbers):
{json.dumps(stats, indent=2, default=str)}

RAW DATA SAMPLE (first 5 and last 5 data points):
{json.dumps(sample, indent=2, default=str)}

YOUR TASK:
Write exactly 3 numbered insights. Rules:
1. Every insight references a specific number from the statistics above.
2. Insight 1: The single most important finding — name the top/bottom performer or the strongest trend.
3. Insight 2: A comparison or context — how does the top compare to the average? Is the trend accelerating or slowing?
4. Insight 3: A specific actionable recommendation — what should the user investigate or do based on this data?
5. Never write generic sentences. Every sentence must be unique to this specific chart's data.
6. Never start with "This chart shows" or "The chart displays".
7. If you see the top value, name it. If you see an outlier, describe it specifically.
8. Write for a business decision maker, not a data scientist.

CRITICAL: If the data has fewer than 3 points, still write 3 insights focused on what the data does show."""

    logger.info(f"[GPT INSIGHT] generate_real_insight called for chart: {chart_title!r}")

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior data analyst. You write specific, number-backed insights. "
                        "You never write generic observations. "
                        "You always name specific values from the data."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.3,
        )
        insight_text = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens
        logger.info(f"[GPT INSIGHT SUCCESS] {chart_title!r} — {tokens_used} tokens")
        return {
            "insight": insight_text,
            "computed_statistics": stats,
            "model": "gpt-4o",
            "tokens_used": tokens_used,
            "is_ai_generated": True,
        }

    except Exception as e:
        logger.error(
            f"[GPT INSIGHT FAILED] {chart_title!r} — {type(e).__name__}: {e}"
        )
        return {
            "insight": _generate_statistical_fallback(stats, chart_title, x_col, y_col),
            "computed_statistics": stats,
            "model": "statistical_fallback",
            "tokens_used": None,
            "is_ai_generated": False,
            "error": str(e),
        }
