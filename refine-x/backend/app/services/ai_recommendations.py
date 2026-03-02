"""
AI Recommendation Engine — Stage 4: Strict JSON chart specifications.
Uses GPT-4o to suggest chart column pairings based on user's analytical goal.
"""

import json
import re

from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Fixed allowed chart types - ChartEngine must support all of these
ALLOWED_CHART_TYPES = [
    "bar",
    "horizontal_bar", 
    "line",
    "scatter",
    "pie",
    "donut",
    "stacked_bar",
    "area",
    "heatmap",
]


def _parse_json(text: str):
    clean = re.sub(r"```[a-z]*\n?", "", text).strip()
    return json.loads(clean)


def recommend_headers(
    column_names: list[str],
    data_sample: list[dict],
    user_goal: str,
) -> list[dict]:
    """
    Stage 4: Returns strict JSON chart specifications.
    
    Each item:
    {
        "chart_title": str,
        "chart_type": str (from ALLOWED_CHART_TYPES),
        "x_column": str,
        "y_column": str | null,
        "reason": str
    }
    
    ChartEngine reads this JSON directly without further GPT calls.
    """
    columns_text = ", ".join(f'"{c}"' for c in column_names)
    sample_text = json.dumps(data_sample[:5], default=str, indent=2)
    chart_types_text = ", ".join(ALLOWED_CHART_TYPES)

    prompt = f"""You are a data analyst helping a user visualize their data.

Dataset columns: [{columns_text}]
Sample data (first 5 rows):
{sample_text}

User's analytical goal: "{user_goal}"

Recommend exactly 5 chart specifications that would create the most useful visualizations for this goal.

ALLOWED chart types (use ONLY these exact values): {chart_types_text}

For pie/donut charts, set y_column to null.

Return ONLY this exact JSON structure (no other text):
[
  {{
    "chart_title": "Revenue by Store",
    "chart_type": "bar",
    "x_column": "store_name",
    "y_column": "revenue",
    "reason": "Compare revenue across stores"
  }}
]

Rules:
- Only use column names that actually exist in the dataset
- chart_type MUST be from the allowed list above
- chart_title should be descriptive and specific
- reason should explain why this chart answers the user's goal"""

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1500,
    )

    result = _parse_json(response.choices[0].message.content)
    
    # Ensure it's a list
    if isinstance(result, dict):
        result = list(result.values())[0] if result else []
    
    # Validate and normalize results
    validated = []
    for item in result[:5]:
        # Validate chart_type
        chart_type = item.get("chart_type", "bar").lower()
        if chart_type not in ALLOWED_CHART_TYPES:
            chart_type = "bar"  # fallback
        
        # Validate columns exist
        x_col = item.get("x_column") or item.get("x_col")
        y_col = item.get("y_column") or item.get("y_col")
        
        if x_col not in column_names:
            continue  # skip invalid recommendations
        
        if y_col and y_col not in column_names:
            y_col = None
            
        validated.append({
            "chart_title": item.get("chart_title", f"{y_col or 'Count'} by {x_col}"),
            "chart_type": chart_type,
            "x_column": x_col,
            "y_column": y_col,
            "reason": item.get("reason", item.get("reasoning", ""))
        })
    
    return validated
