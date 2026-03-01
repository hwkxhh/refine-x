"""
AI Recommendation Engine — uses GPT-4o to suggest chart column pairings
based on user's analytical goal.
"""

import json
import re

from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _parse_json(text: str):
    clean = re.sub(r"```[a-z]*\n?", "", text).strip()
    return json.loads(clean)


def recommend_headers(
    column_names: list[str],
    data_sample: list[dict],
    user_goal: str,
) -> list[dict]:
    """
    Returns 5 recommended X/Y column pairings.

    Each item:
    {
        "x_col": str,
        "y_col": str | null,
        "chart_type": str,
        "relevance_score": float (0-1),
        "reasoning": str
    }
    """
    columns_text = ", ".join(f'"{c}"' for c in column_names)
    sample_text = json.dumps(data_sample[:5], default=str, indent=2)

    prompt = f"""You are a data analyst helping a user visualize their data.

Dataset columns: [{columns_text}]
Sample data (first 5 rows):
{sample_text}

User's analytical goal: "{user_goal}"

Recommend exactly 5 X vs Y column pairings that would create the most useful and relevant charts for this goal.
For pie charts, only provide x_col and set y_col to null.

Return ONLY valid JSON array:
[
  {{
    "x_col": "column_name",
    "y_col": "column_name_or_null",
    "chart_type": "line|bar|scatter|pie",
    "relevance_score": 0.95,
    "reasoning": "Why this pairing is relevant to the user's goal"
  }}
]

Only use column names that actually exist in the dataset."""

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1200,
    )

    result = _parse_json(response.choices[0].message.content)
    # Ensure it's a list
    if isinstance(result, dict):
        result = list(result.values())[0] if result else []
    return result[:5]
