"""
AI Insight Generator — uses GPT-4o to generate natural language insights
for charts, with confidence scoring and actionable recommendations.
"""

import json
import re

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


def generate_chart_insight(
    chart_type: str,
    x_header: str,
    y_header: str | None,
    chart_data: list[dict],
    user_goal: str,
) -> dict:
    """
    Generate a natural-language insight for a chart.

    Returns:
    {
        "insight": str,
        "confidence_score": float,
        "confidence": str,
        "recommendations": [{"action": str, "reasoning": str}]
    }
    """
    # Build data summary stats
    import pandas as pd
    import numpy as np

    df = pd.DataFrame(chart_data)
    stats = {}
    if "y" in df.columns:
        y_num = pd.to_numeric(df["y"], errors="coerce").dropna()
        if len(y_num) > 0:
            stats = {
                "mean": round(float(y_num.mean()), 4),
                "median": round(float(y_num.median()), 4),
                "min": round(float(y_num.min()), 4),
                "max": round(float(y_num.max()), 4),
                "total": round(float(y_num.sum()), 4),
            }

    data_preview = json.dumps(chart_data[:10], default=str)
    stats_text = json.dumps(stats) if stats else "N/A"
    y_label = y_header or "count"

    confidence_instructions = (
        "If you are highly confident in the insight (clear trend/pattern), set confidence_score 0.7-1.0. "
        "If moderately confident, set 0.4-0.7. If the data is unclear or limited, set 0.0-0.4 and use hedging language."
    )

    prompt = f"""You are analyzing a {chart_type} chart.
X-axis: "{x_header}", Y-axis: "{y_label}"
User's analytical goal: "{user_goal}"

Data summary statistics: {stats_text}
Data sample (up to 10 points): {data_preview}

Analyze this chart and provide:
1. What pattern or trend is visible in the data?
2. How does this relate to the user's goal?
3. Two or three specific, actionable recommendations.

{confidence_instructions}

Return ONLY valid JSON:
{{
  "insight": "Natural language analysis of the chart...",
  "confidence_score": 0.85,
  "recommendations": [
    {{"action": "Action to take", "reasoning": "Why this action is recommended"}}
  ]
}}"""

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1000,
    )

    result = _parse_json(response.choices[0].message.content)
    score = float(result.get("confidence_score", 0.5))
    result["confidence"] = _confidence_category(score)
    result["confidence_score"] = round(score, 3)
    return result


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
