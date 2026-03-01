"""
AI Analysis Service — uses OpenAI GPT-4o to:
1. Identify unnecessary/redundant columns in a dataset
2. Suggest appropriate formulas/analyses for the data
"""

import json
import re
from typing import Optional

from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _parse_json_from_response(text: str) -> dict | list:
    """Robustly extract JSON from GPT response even if it's wrapped in markdown."""
    # Strip markdown code fences
    clean = re.sub(r"```[a-z]*\n?", "", text).strip()
    return json.loads(clean)


def analyze_headers(
    columns: list[str],
    sample_rows: list[dict],
    filename: str,
) -> dict:
    """
    Ask GPT-4o which columns are unnecessary for analysis/visualization.

    Returns:
    {
        "unnecessary_columns": [
            {
                "column": str,
                "reason": str,
                "impact_if_removed": str   # e.g. "None — this is a row ID"
            }
        ],
        "essential_columns": [str, ...],
        "dataset_summary": str
    }
    """
    sample_text = json.dumps(sample_rows[:5], default=str, indent=2)
    columns_text = ", ".join(f'"{c}"' for c in columns)

    prompt = f"""You are a data analyst reviewing a dataset from file: "{filename}".

Columns: [{columns_text}]

Sample data (first 5 rows):
{sample_text}

Your task:
1. Identify any columns that are UNNECESSARY for data analysis or visualization. 
   These are typically: row IDs, auto-increment numbers, internal system fields, duplicate info, 
   freeform notes that can't be charted, or columns with near-zero analytical value.
2. For EACH unnecessary column explain WHY it is not needed and what impact removing it would have.
3. List all columns that ARE essential/useful.
4. Write a 1-2 sentence summary of what this dataset contains.

Return ONLY valid JSON in this exact format:
{{
  "unnecessary_columns": [
    {{
      "column": "column_name",
      "reason": "why this column is not useful",
      "impact_if_removed": "None - this is just a row number"
    }}
  ],
  "essential_columns": ["col1", "col2"],
  "dataset_summary": "This dataset contains..."
}}"""

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1500,
    )

    return _parse_json_from_response(response.choices[0].message.content)


def suggest_formulas(
    columns: list[str],
    sample_rows: list[dict],
    filename: str,
    dataset_summary: Optional[str] = None,
) -> dict:
    """
    Ask GPT-4o to suggest appropriate analyses and formulas for this dataset.

    Returns:
    {
        "suggested_analyses": [
            {
                "name": str,             # e.g. "Monthly Sales Trend"
                "description": str,
                "columns_needed": [str],
                "formula_type": str,     # e.g. "SUM", "AVERAGE", "COUNT", "PERCENTAGE CHANGE"
                "example": str
            }
        ],
        "recommended_visualizations": [
            {
                "chart_type": str,
                "x_column": str,
                "y_column": str,
                "reason": str
            }
        ]
    }
    """
    sample_text = json.dumps(sample_rows[:5], default=str, indent=2)
    columns_text = ", ".join(f'"{c}"' for c in columns)
    summary_line = f"\nDataset summary: {dataset_summary}" if dataset_summary else ""

    prompt = f"""You are a data analyst reviewing a dataset from file: "{filename}".{summary_line}

Columns: [{columns_text}]

Sample data (first 5 rows):
{sample_text}

Suggest:
1. The most useful calculations/formulas to apply to this data (e.g. totals, averages, growth rates, percentages)
2. The best chart/visualization pairings for this data

Return ONLY valid JSON in this exact format:
{{
  "suggested_analyses": [
    {{
      "name": "Total Revenue by Category",
      "description": "Sum of revenue grouped by product category",
      "columns_needed": ["category", "revenue"],
      "formula_type": "SUM + GROUPBY",
      "example": "SUM(revenue) GROUP BY category"
    }}
  ],
  "recommended_visualizations": [
    {{
      "chart_type": "bar",
      "x_column": "category",
      "y_column": "revenue",
      "reason": "Compare revenue across categories"
    }}
  ]
}}

Provide 3-5 suggested analyses and 3-5 recommended visualizations."""

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2000,
    )

    return _parse_json_from_response(response.choices[0].message.content)
