"""
Role-Based Chart Suite Generator — domain-agnostic automatic chart production.

Given a DataFrame and its column role map (from get_plottable_columns()),
this module produces the complete set of charts a professional analyst would
create.  It never produces a chart that uses an identifier, sequence, constant,
or code column as an axis.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from app.services.column_role_classifier import get_plottable_columns


# ── Label helper ──────────────────────────────────────────────────────────────

def _human_label(col_name: str) -> str:
    return col_name.replace("_", " ").replace("-", " ").title()


# ── Signature helper (dedup key) ──────────────────────────────────────────────

def _chart_sig(x: str | None, y: str | None, chart_type: str) -> str:
    return f"{(x or '').lower()}|{(y or '').lower()}|{chart_type.lower()}"


# ── Metric ranking ────────────────────────────────────────────────────────────

def _rank_metrics(df: pd.DataFrame, metric_cols: list[str]) -> list[str]:
    """
    Rank metrics by analytical importance.
    Prefer totals, revenue, profit, count over derived/helper columns.
    Deprioritise row numbers, sequences, percentages already represented.
    """
    priority_kw = [
        "revenue", "sales", "amount", "profit", "income", "cost",
        "salary", "payroll", "payment", "earning",
        "count", "total", "sum", "number", "quantity", "volume",
        "score", "grade", "rate", "patients", "students", "employees",
        "establishments", "beds", "admissions", "orders",
    ]
    depriority_kw = ["id", "no", "seq", "index", "row", "rank", "code"]

    def _score(col: str) -> int:
        c = col.lower()
        return sum(2 for kw in priority_kw if kw in c) + sum(-3 for kw in depriority_kw if kw in c)

    return sorted(metric_cols, key=_score, reverse=True)


# ── Scatter pair finder ───────────────────────────────────────────────────────

def _find_meaningful_metric_pairs(
    df: pd.DataFrame,
    metrics: list[str],
) -> list[tuple[str, str]]:
    """
    Find metric pairs worth scattering.
    Skips pairs with no detectable correlation (|r| ≤ 0.1).
    """
    pairs: list[tuple[str, str, float]] = []
    for i in range(len(metrics)):
        for j in range(i + 1, len(metrics)):
            x, y = metrics[i], metrics[j]
            try:
                x_num = pd.to_numeric(df[x], errors="coerce").dropna()
                y_num = pd.to_numeric(df[y], errors="coerce").dropna()
                if len(x_num) < 10 or len(y_num) < 10:
                    continue
                aligned = pd.concat([x_num, y_num], axis=1).dropna()
                if len(aligned) < 10:
                    continue
                corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
                if abs(corr) > 0.1:
                    pairs.append((x, y, abs(corr)))
            except Exception:
                continue
    pairs.sort(key=lambda p: p[2], reverse=True)
    return [(p[0], p[1]) for p in pairs]


# ── Bar type selector ─────────────────────────────────────────────────────────

def _pick_bar_type(n_unique: int) -> str:
    return "bar" if n_unique <= 7 else "horizontal_bar"


# ── Reason builders ───────────────────────────────────────────────────────────

def _bar_reason(
    chart_type: str, cat_col: str, metric: str, n_unique: int, limit: int | None
) -> str:
    limit_note = f" Top {limit} shown." if limit else ""
    if chart_type == "horizontal_bar":
        return (
            f"Horizontal bar because {_human_label(cat_col)} has {n_unique} unique values "
            f"— names need horizontal space to be readable. "
            f"Sorted descending to show ranking.{limit_note}"
        )
    return (
        f"Vertical bar comparing {_human_label(metric)} across {n_unique} "
        f"{_human_label(cat_col)} groups. "
        f"Sorted descending for immediate ranking visibility."
    )


# ── Dedup and quality filter ──────────────────────────────────────────────────

def _dedup_charts(charts: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    result: list[dict] = []
    for c in charts:
        key = (c.get("x"), c.get("y"), c.get("type"))
        if key not in seen:
            seen.add(key)
            result.append(c)
    return result


def _filter_empty_charts(charts: list[dict], df: pd.DataFrame) -> list[dict]:
    """Remove chart specs whose columns contain no usable data."""
    result: list[dict] = []
    for c in charts:
        x_col = c.get("x")
        y_col = c.get("y")
        if y_col == "count":
            result.append(c)
            continue
        if x_col in df.columns and y_col in df.columns:
            x_valid = df[x_col].notna().sum()
            y_valid = pd.to_numeric(df[y_col], errors="coerce").notna().sum()
            if x_valid > 0 and y_valid > 0:
                result.append(c)
    return result


# ── Core engine ───────────────────────────────────────────────────────────────

def generate_charts_from_roles(
    df: pd.DataFrame,
    col_map: dict,
    goal: str = "",
) -> list[dict]:
    """
    Generate meaningful charts using column roles.
    Never produces a chart that a data analyst would reject.

    col_map must be the output of get_plottable_columns(df).
    Returns internal-format chart specs with keys: type, x, y, title, reason.
    The public API (generate_full_chart_suite) normalises these to
    chart_type / x_col / y_col for ChartEngine compatibility.
    """
    charts: list[dict] = []
    date_cols: list[str] = col_map["date_cols"]
    category_cols: list[str] = col_map["category_cols"]
    metric_cols: list[str] = col_map["metric_cols"]
    code_cols: list[str] = col_map["code_cols"]

    # Rank metrics — put totals / primary measures first, cap at 4
    primary_metrics = _rank_metrics(df, metric_cols)[:4]

    # ── CHART SET 1: Time series — Date × Metric ──────────────────────────
    # One line chart per primary metric per date column.
    # Cap at 4 time-series charts total to avoid overload.
    time_charts_added = 0
    for date_col in date_cols[:2]:
        for metric in primary_metrics:
            if time_charts_added >= 4:
                break
            charts.append({
                "title": f"{_human_label(metric)} Over Time",
                "type": "line",
                "x": date_col,
                "y": metric,
                "aggregate": True,
                "agg_func": "sum",
                "sort": "asc",
                "reason": (
                    f"Line chart tracking {_human_label(metric)} over time. "
                    f"Aggregated to appropriate time period. Lines show continuity "
                    f"and trend direction — bars would incorrectly imply each "
                    f"period is independent."
                ),
            })
            time_charts_added += 1

        # Volume over time: count of records per period
        charts.append({
            "title": "Volume Over Time",
            "type": "bar",
            "x": date_col,
            "y": "count",
            "aggregate": True,
            "sort": "asc",
            "reason": (
                "Bar chart counting records per time period. "
                "Bars communicate discrete event counting better than a continuous line."
            ),
        })

    # ── CHART SET 2: Category breakdown — Category × Metric ───────────────
    # Only use categories with cardinality 2–200.
    for cat_col in category_cols:
        n_unique = df[cat_col].nunique()
        if n_unique < 2 or n_unique > 200:
            continue

        chart_type = _pick_bar_type(n_unique)
        limit = None if n_unique <= 15 else 10

        for metric in primary_metrics[:3]:
            charts.append({
                "title": f"{_human_label(metric)} by {_human_label(cat_col)}",
                "type": chart_type,
                "x": cat_col if chart_type == "bar" else metric,
                "y": metric if chart_type == "bar" else cat_col,
                "sort": "desc",
                "limit": limit,
                "reason": _bar_reason(chart_type, cat_col, metric, n_unique, limit),
            })

        # Count per category: donut (≤6) or bar/horizontal_bar (>6)
        if n_unique <= 6:
            charts.append({
                "title": f"Distribution by {_human_label(cat_col)}",
                "type": "donut",
                "x": cat_col,
                "y": "count",
                "reason": (
                    f"Donut chart showing proportion of records by "
                    f"{_human_label(cat_col)}. {n_unique} categories is within "
                    f"the readable limit of 6 for pie/donut charts."
                ),
            })
        else:
            charts.append({
                "title": f"Count by {_human_label(cat_col)}",
                "type": chart_type,
                "x": cat_col if chart_type == "bar" else "count",
                "y": "count" if chart_type == "bar" else cat_col,
                "sort": "desc",
                "limit": limit,
                "reason": f"Count of records per {_human_label(cat_col)} category.",
            })

    # ── CHART SET 3: Metric vs Metric — Scatter ───────────────────────────
    # Only pair metrics with a detectable correlation (|r| > 0.1).
    # Never scatter a metric against a code or sequence.
    scatter_pairs = _find_meaningful_metric_pairs(df, primary_metrics)
    for x_metric, y_metric in scatter_pairs[:3]:
        charts.append({
            "title": f"{_human_label(y_metric)} vs {_human_label(x_metric)}",
            "type": "scatter",
            "x": x_metric,
            "y": y_metric,
            "reason": (
                f"Scatter plot to reveal whether {_human_label(x_metric)} and "
                f"{_human_label(y_metric)} are correlated. Shows the relationship "
                f"at individual record level — outliers and clusters are visible."
            ),
        })

    # ── CHART SET 4: Low-cardinality code columns ─────────────────────────
    # NAICS code with 5 unique values → bar.
    # NAICS code with 500 unique values → skip entirely.
    for code_col in code_cols:
        n_unique = df[code_col].nunique()
        if n_unique <= 20:
            chart_type = "horizontal_bar" if n_unique > 7 else "bar"
            for metric in primary_metrics[:2]:
                charts.append({
                    "title": f"{_human_label(metric)} by {_human_label(code_col)}",
                    "type": chart_type,
                    "x": code_col if n_unique <= 7 else metric,
                    "y": metric if n_unique <= 7 else code_col,
                    "sort": "desc",
                    "reason": (
                        f"{_human_label(code_col)} has {n_unique} unique values "
                        f"— readable as a bar chart. Code values represent categories "
                        f"even though they look numeric."
                    ),
                })

    # ── Dedup and quality filter ───────────────────────────────────────────
    charts = _dedup_charts(charts)
    charts = _filter_empty_charts(charts, df)
    return charts[:15]


# ── Public API ────────────────────────────────────────────────────────────────

def generate_full_chart_suite(
    df: pd.DataFrame,
    htypes: Optional[dict] = None,
    goal: str = "",
    existing_charts: Optional[list[dict]] = None,
    derived_columns: Optional[list[dict]] = None,
) -> list[dict]:
    """
    Produce the full analyst-grade chart suite for any dataset.

    Args:
        df:               The cleaned DataFrame.
        htypes:           Reserved — not used by the role-based engine.
        goal:             User's analytical goal text (reserved for future use).
        existing_charts:  Already-generated chart dicts for dedup.
        derived_columns:  Metadata list from compute_all_derived_metrics().

    Returns:
        List of chart spec dicts ready to be passed to ChartEngine:
        [
            {
                "title":      str,
                "chart_type": str,
                "x_col":      str,
                "y_col":      str | None,
                "group_by":   None,
                "reason":     str,
            },
            ...
        ]
    """
    # ── Role-gate every column ────────────────────────────────────────────
    col_map = get_plottable_columns(df)

    # ── Generate role-based charts ────────────────────────────────────────
    raw_charts = generate_charts_from_roles(df, col_map, goal=goal)

    # ── Derived-metric charts (same rules as regular metrics) ─────────────
    for derived in (derived_columns or []):
        d_name = derived.get("name", "")
        d_label = derived.get("label", _human_label(d_name))
        source = derived.get("source_columns", [])

        if d_name not in df.columns:
            continue

        for date_col in col_map["date_cols"][:1]:
            raw_charts.append({
                "title": f"{d_label} Over Time",
                "type": "line",
                "x": date_col,
                "y": d_name,
                "reason": (
                    f"Derived metric '{d_label}' plotted over time. Shows whether "
                    f"the computed ratio/rate is improving, declining, or stable."
                ),
            })

        for cat_col in col_map["category_cols"]:
            if df[cat_col].nunique() <= 15:
                ct = "bar" if df[cat_col].nunique() <= 7 else "horizontal_bar"
                raw_charts.append({
                    "title": f"{d_label} by {_human_label(cat_col)}",
                    "type": ct,
                    "x": cat_col,
                    "y": d_name,
                    "reason": (
                        f"{d_label} grouped by {cat_col}. "
                        f"Derived metric from source columns: "
                        f"{', '.join(source)}."
                    ),
                })

    raw_charts = _dedup_charts(raw_charts)[:15]

    # ── Normalise internal format → ChartEngine format ────────────────────
    # Internal keys: type / x / y
    # External keys: chart_type / x_col / y_col
    def _norm(spec: dict) -> dict:
        y = spec.get("y")
        return {
            "title": spec.get("title", ""),
            "chart_type": spec.get("type", "bar"),
            "x_col": spec.get("x"),
            "y_col": None if y == "count" else y,
            "group_by": spec.get("group_by"),
            "reason": spec.get("reason", ""),
        }

    normalised = [_norm(s) for s in raw_charts]

    # ── Deduplicate against already-existing charts ────────────────────────
    existing_sigs: set[str] = set()
    if existing_charts:
        for ec in existing_charts:
            sig = _chart_sig(
                ec.get("x_col", ec.get("x_header", "")),
                ec.get("y_col", ec.get("y_header", "")),
                ec.get("chart_type", ""),
            )
            existing_sigs.add(sig)

    suite: list[dict] = []
    seen_sigs: set[str] = set()

    for spec in normalised:
        sig = _chart_sig(spec["x_col"], spec.get("y_col"), spec["chart_type"])
        if sig in existing_sigs or sig in seen_sigs:
            continue

        # Validate columns still exist in df
        if not spec["x_col"] or spec["x_col"] not in df.columns:
            continue
        y = spec.get("y_col")
        if y and y not in df.columns:
            continue

        seen_sigs.add(sig)
        suite.append(spec)

    return suite
