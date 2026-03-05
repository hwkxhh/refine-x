"""
ChartEngine — determines chart type and generates Recharts-compatible data.
Supports grouped (multi-series) line/area/scatter charts for longitudinal data.
Also generates correlation heatmap.
"""

import warnings
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from app.services.chart_type_rules import determine_chart_type as _rulebook_determine

def _is_year_like(vals) -> bool:
    """True if all values look like years (1800–2100)."""
    try:
        nums = pd.to_numeric(pd.Series(vals).dropna(), errors="coerce").dropna()
        return not nums.empty and bool((nums >= 1800).all() and (nums <= 2100).all())
    except Exception:
        return False


def _axis_domain(vals, is_year: bool) -> list:
    """
    Compute a sensible [min, max] domain for an axis.
    For year/date axes: start at min-1, end at max+1 (never zero-based).
    For regular numeric: use dataMin / dataMax with 5% padding.
    """
    nums = [v for v in vals if isinstance(v, (int, float)) and not np.isnan(v)]
    if not nums:
        return [0, 1]
    lo, hi = min(nums), max(nums)
    if is_year:
        return [lo - 1, hi + 1]
    span = hi - lo or 1
    pad = span * 0.05
    return [lo - pad, hi + pad]


def _detect_y_unit(col_name: str | None) -> str:
    """Infer the y-axis unit from column name for frontend formatting."""
    if not col_name:
        return "count"
    name = str(col_name).lower().replace("_", " ").replace("-", " ")
    if any(kw in name for kw in ["pct", "percent", "rate", "ratio", "margin"]):
        return "percent"
    if any(kw in name for kw in ["amount", "revenue", "sales", "price", "cost",
                                  "profit", "salary", "income", "wage", "payment",
                                  "spend", "budget", "fee", "charge"]):
        return "currency"
    return "plain"


# ── Date detection & aggregation engine ──────────────────────────────────────

DATE_SPAN_RULES = [
    {"max_days": 1,     "freq": "h",  "strftime": "%H:00 %d %b",  "label": "Hourly"},
    {"max_days": 31,    "freq": "D",  "strftime": "%d %b %Y",     "label": "Daily"},
    {"max_days": 90,    "freq": "W",  "strftime": "W%W %Y",       "label": "Weekly"},
    {"max_days": 1825,  "freq": "M",  "strftime": "%b %Y",        "label": "Monthly"},
    {"max_days": 3650,  "freq": "Q",  "strftime": None,           "label": "Quarterly"},
    {"max_days": 99999, "freq": "Y",  "strftime": "%Y",           "label": "Yearly"},
]


def _is_date_column(col_name: str, series: pd.Series) -> bool:
    """True if column contains parseable dates that need time-aggregation.
    Year-like integer columns (2020, 2021) are already aggregated — skip.
    Purely-numeric columns (Amount, Price) are never dates."""
    if _is_year_like(series):
        return False
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    name = str(col_name).lower().replace("_", " ").replace("-", " ")
    date_kw = ["date", "datetime", "timestamp", "created", "updated", "ordered"]
    has_hint = any(k in name for k in date_kw)
    sample = series.dropna().head(50)
    # Reject purely-numeric columns that don't have a date keyword in the name
    if not has_hint and pd.to_numeric(sample, errors="coerce").notna().mean() >= 0.8:
        return False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(sample, errors="coerce")
        ratio = parsed.notna().mean()
        return ratio >= 0.5 if has_hint else ratio >= 0.7
    except Exception:
        return False


def get_aggregation_rule(date_series: pd.Series) -> dict:
    """Pick the correct time-bucket granularity based on date span."""
    dates = pd.to_datetime(date_series, errors="coerce").dropna()
    if len(dates) < 2:
        return DATE_SPAN_RULES[3]  # default Monthly
    span = (dates.max() - dates.min()).days
    for rule in DATE_SPAN_RULES:
        if span <= rule["max_days"]:
            return rule
    return DATE_SPAN_RULES[-1]


def aggregate_time_series(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    agg_func: str = "sum",
    group_by: Optional[str] = None,
) -> Tuple[pd.DataFrame, str, str]:
    """
    Aggregate any time-series to the correct granularity.
    Works for any domain, any date column, any value column.
    Returns (aggregated_df, x_col_name, aggregation_label).
    The x column in the returned df contains formatted string labels,
    never raw timestamps.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    rule = get_aggregation_rule(df[date_col])

    # Create time-bucket column
    df["_time_bucket"] = df[date_col].dt.to_period(rule["freq"]).dt.to_timestamp()

    group_cols = ["_time_bucket"]
    if group_by and group_by in df.columns:
        group_cols.append(group_by)

    # Aggregate
    if value_col == "count":
        agg_df = df.groupby(group_cols).size().reset_index(name="count")
    else:
        num_col = "_y_agg"
        df[num_col] = pd.to_numeric(df[value_col], errors="coerce")
        agg_df = df.groupby(group_cols)[num_col].agg(agg_func).reset_index()
        agg_df = agg_df.rename(columns={num_col: value_col})

    # Format x labels — NEVER return raw timestamps
    if rule["freq"] == "Q":
        agg_df["_time_label"] = (
            agg_df["_time_bucket"].dt.to_period("Q").astype(str)
        )
    else:
        agg_df["_time_label"] = agg_df["_time_bucket"].dt.strftime(rule["strftime"])

    agg_df = agg_df.drop(columns=["_time_bucket"])
    agg_df = agg_df.rename(columns={"_time_label": date_col})
    agg_df = agg_df.sort_values(date_col)

    return agg_df, date_col, rule["label"]


class ChartEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def determine_chart_type(self, x_col: str, y_col: str | None = None, group_by: str | None = None) -> str:
        """Return the best chart type for the given column pairing using the analyst rulebook."""
        result = _rulebook_determine(x_col, y_col, self.df, group_by=group_by)
        return result["chart_type"]

    def generate_chart_data(
        self,
        x_col: str,
        y_col: str | None,
        chart_type: str,
        group_by: str | None = None,
    ) -> dict:
        """
        Generate Recharts-compatible data payload.

        When group_by is provided (longitudinal data), returns multi-series
        data where each series key is a unique value from the group_by column.
        Recharts can render this as multiple <Line> / <Bar> components.
        """
        df = self.df.copy()

        x_label = str(x_col).replace("_", " ").title()
        y_label = str(y_col).replace("_", " ").title() if y_col else "Count"

        # ── Pie / Donut / no y-col ────────────────────────────────────────
        if chart_type in ("pie", "donut") or not y_col:
            counts = df[x_col].value_counts().head(20)
            data = [{"name": str(k), "value": int(v)} for k, v in counts.items()]
            title = f"Distribution of {x_label}"
            return {
                "data": data, "xLabel": x_label, "yLabel": "Count",
                "title": title, "grouped": False,
                "data_key": "value", "y_unit": "count",
            }

        x_is_numeric = pd.to_numeric(df[x_col], errors="coerce").notna().mean() >= 0.8
        x_is_year = _is_year_like(df[x_col].dropna().head(50))

        # ── GROUPED (multi-series) — also used for stacked_bar ───────────
        if group_by and group_by in df.columns and group_by != x_col:
            x_is_date = _is_date_column(x_col, df[x_col])
            df["_y_num"] = pd.to_numeric(df[y_col], errors="coerce")

            groups = df[group_by].dropna().unique().tolist()

            # Limit to top-N groups by sum of y to keep charts readable
            MAX_GROUPS = 10
            note = None
            if len(groups) > MAX_GROUPS:
                top_groups = (
                    df.groupby(group_by)["_y_num"].sum()
                    .nlargest(MAX_GROUPS).index.tolist()
                )
                note = f"Showing top {MAX_GROUPS} {group_by.replace('_', ' ')} by {y_label}."
                groups = top_groups

            df_filtered = df[df[group_by].isin(groups)]

            if x_is_date:
                # ── Date x-axis: aggregate then pivot ─────────────────────
                agg_df, _, agg_label = aggregate_time_series(
                    df_filtered, x_col, y_col,
                    agg_func="mean", group_by=group_by,
                )
                pivot = agg_df.pivot_table(
                    index=x_col, columns=group_by, values=y_col,
                    aggfunc="mean",
                ).reset_index().sort_values(x_col)
                pivot.columns.name = None
                x_key = x_col
                title_extra = f" ({agg_label})"
                x_domain = None
            else:
                # ── Categorical / numeric x-axis ──────────────────────────
                df_filtered = df_filtered.copy()
                df_filtered["_x_val"] = (
                    pd.to_numeric(df_filtered[x_col], errors="coerce")
                    if x_is_numeric
                    else df_filtered[x_col].astype(str)
                )
                pivot = (
                    df_filtered.groupby(["_x_val", group_by])["_y_num"]
                    .mean().reset_index()
                    .pivot(index="_x_val", columns=group_by, values="_y_num")
                    .reset_index().sort_values("_x_val")
                )
                pivot.columns.name = None
                x_key = "_x_val"
                title_extra = ""
                x_vals_raw = [row[x_key] for _, row in pivot.iterrows()]
                x_domain = _axis_domain(x_vals_raw, x_is_year)

            data = []
            for _, row in pivot.iterrows():
                point = {"x": str(row[x_key])}
                for g in groups:
                    v = row.get(g, None)
                    point[str(g)] = round(float(v), 4) if pd.notna(v) else None
                data.append(point)

            all_y = [v for p in data for k, v in p.items() if k != "x" and v is not None]
            y_domain = _axis_domain(all_y, False)

            return {
                "data": data,
                "xLabel": x_label,
                "yLabel": y_label,
                "title": f"{y_label} over {x_label} by {str(group_by).replace('_', ' ').title()}{title_extra}",
                "grouped": True,
                "series_keys": [str(g) for g in groups],
                "xDomain": x_domain,
                "yDomain": y_domain,
                "note": note,
                "data_key": "grouped", "y_unit": _detect_y_unit(y_col),
            }

        # ── SCATTER ───────────────────────────────────────────────────────
        if chart_type == "scatter":
            df["_x"] = pd.to_numeric(df[x_col], errors="coerce")
            df["_y"] = pd.to_numeric(df[y_col], errors="coerce")
            subset = df[["_x", "_y"]].dropna()
            if len(subset) > 400:
                subset = subset.sample(400, random_state=42)
            x_key = x_col
            y_key = y_col
            data = [
                {x_key: round(float(r["_x"]), 4), y_key: round(float(r["_y"]), 4)}
                for _, r in subset.iterrows()
            ]
            title = f"{y_label} vs {x_label}"
            x_vals = [p[x_key] for p in data]
            y_vals = [p[y_key] for p in data]
            return {
                "data": data, "xLabel": x_label, "yLabel": y_label, "title": title,
                "grouped": False,
                "xDomain": _axis_domain(x_vals, _is_year_like(x_vals)),
                "yDomain": _axis_domain(y_vals, _is_year_like(y_vals)),
                "data_key": y_key, "x_data_key": x_key,
                "y_unit": _detect_y_unit(y_col),
            }

        # ── LINE / AREA ────────────────────────────────────────────────────
        if chart_type in ("line", "area"):
            x_is_date = _is_date_column(x_col, df[x_col])

            if x_is_date:
                agg_df, _, agg_label = aggregate_time_series(
                    df, x_col, y_col, agg_func="mean",
                )
                y_key = y_col
                data = [
                    {"x": str(r[x_col]), y_key: round(float(r[y_col]), 4)}
                    for _, r in agg_df.iterrows() if pd.notna(r[y_col])
                ]
                title = f"{y_label} over {x_label} ({agg_label})"
                y_vals = [p[y_key] for p in data]
                return {
                    "data": data, "xLabel": x_label, "yLabel": y_label,
                    "title": title, "grouped": False,
                    "xDomain": None,
                    "yDomain": _axis_domain(y_vals, False),
                    "data_key": y_key, "y_unit": _detect_y_unit(y_col),
                }

            # Non-date axis: original numeric / categorical groupby
            y_key = y_col
            df["_y_num"] = pd.to_numeric(df[y_col], errors="coerce")
            grouped = df.groupby(x_col)["_y_num"].mean().reset_index()
            if x_is_numeric or x_is_year:
                grouped["_x_sort"] = pd.to_numeric(grouped[x_col], errors="coerce")
                grouped = grouped.sort_values("_x_sort")
            else:
                grouped = grouped.sort_values(x_col)
            data = [
                {"x": (float(r[x_col]) if (x_is_numeric or x_is_year) else str(r[x_col])),
                 y_key: round(float(r["_y_num"]), 4)}
                for _, r in grouped.iterrows() if pd.notna(r["_y_num"])
            ]
            title = f"{y_label} over {x_label}"
            x_vals = [p["x"] for p in data]
            y_vals = [p[y_key] for p in data]
            return {
                "data": data, "xLabel": x_label, "yLabel": y_label, "title": title,
                "grouped": False,
                "xDomain": _axis_domain(x_vals, x_is_year),
                "yDomain": _axis_domain(y_vals, False),
                "data_key": y_key, "y_unit": _detect_y_unit(y_col),
            }

        # ── HORIZONTAL BAR ─────────────────────────────────────────────────
        if chart_type == "horizontal_bar":
            x_is_date = _is_date_column(x_col, df[x_col])
            y_key = y_col

            if x_is_date:
                agg_df, _, agg_label = aggregate_time_series(
                    df, x_col, y_col, agg_func="sum",
                )
                agg_df["_y_sort"] = pd.to_numeric(agg_df[y_col], errors="coerce")
                agg_df = agg_df.sort_values("_y_sort", ascending=False).head(30)
                data = [
                    {"x": str(r[x_col]), y_key: round(float(r[y_col]), 4)}
                    for _, r in agg_df.iterrows() if pd.notna(r[y_col])
                ]
                title = f"{y_label} by {x_label} ({agg_label})"
            else:
                df["_y_num"] = pd.to_numeric(df[y_col], errors="coerce")
                agg = df.groupby(x_col)["_y_num"].sum().reset_index()
                agg = agg.sort_values("_y_num", ascending=False).head(30)
                data = [
                    {"x": str(r[x_col]), y_key: round(float(r["_y_num"]), 4)}
                    for _, r in agg.iterrows()
                ]
                title = f"{y_label} by {x_label}"

            y_vals = [p[y_key] for p in data]
            return {
                "data": data, "xLabel": x_label, "yLabel": y_label, "title": title,
                "grouped": False, "layout": "horizontal",
                "xDomain": None,
                "yDomain": _axis_domain(y_vals, False),
                "data_key": y_key, "y_unit": _detect_y_unit(y_col),
            }

        # ── BAR / STACKED_BAR (default) ────────────────────────────────────
        x_is_date = _is_date_column(x_col, df[x_col])
        y_key = y_col

        if x_is_date:
            agg_df, _, agg_label = aggregate_time_series(
                df, x_col, y_col, agg_func="sum",
            )
            data = [
                {"x": str(r[x_col]), y_key: round(float(r[y_col]), 4)}
                for _, r in agg_df.iterrows() if pd.notna(r[y_col])
            ]
            title = f"{y_label} by {x_label} ({agg_label})"
        elif x_is_numeric:
            df["_y_num"] = pd.to_numeric(df[y_col], errors="coerce")
            data = [
                {"x": str(r[x_col]), y_key: round(float(r["_y_num"]), 4) if pd.notna(r["_y_num"]) else 0}
                for _, r in df[[x_col, "_y_num"]].dropna().iterrows()
            ][:50]
            title = f"{y_label} by {x_label}"
        else:
            df["_y_num"] = pd.to_numeric(df[y_col], errors="coerce")
            agg = df.groupby(x_col)["_y_num"].sum().reset_index()
            data = [
                {"x": str(r[x_col]), y_key: round(float(r["_y_num"]), 4)}
                for _, r in agg.iterrows()
            ]
            title = f"{y_label} by {x_label}"

        y_vals = [p[y_key] for p in data]
        return {
            "data": data, "xLabel": x_label, "yLabel": y_label, "title": title,
            "grouped": False,
            "xDomain": None,
            "yDomain": _axis_domain(y_vals, False),
            "data_key": y_key, "y_unit": _detect_y_unit(y_col),
        }

    def generate_correlation_heatmap(self) -> dict:
        """Return correlation matrix for all numeric columns."""
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return {"matrix": [], "columns": []}

        corr = numeric_df.corr()
        columns = corr.columns.tolist()
        matrix = [[round(float(v), 4) for v in row] for row in corr.values]
        return {"matrix": matrix, "columns": columns}
