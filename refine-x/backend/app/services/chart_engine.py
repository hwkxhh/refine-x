"""
ChartEngine — determines chart type and generates Recharts-compatible data.
Also generates correlation heatmap.
"""

import numpy as np
import pandas as pd


class ChartEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def determine_chart_type(self, x_col: str, y_col: str | None = None) -> str:
        """Return the best chart type for the given column pairing."""
        if x_col not in self.df.columns:
            return "bar"

        x_series = self.df[x_col].dropna()

        # No y → pie chart (single categorical distribution)
        if not y_col:
            return "pie"

        if y_col not in self.df.columns:
            return "bar"

        y_numeric = pd.to_numeric(self.df[y_col], errors="coerce").notna().mean() >= 0.8
        x_numeric = pd.to_numeric(x_series, errors="coerce").notna().mean() >= 0.8

        # Try to detect date/time column for x
        x_is_date = False
        if not x_numeric:
            try:
                parsed = pd.to_datetime(x_series.head(20), infer_datetime_format=True, errors="coerce")
                x_is_date = parsed.notna().mean() >= 0.7
            except Exception:
                pass

        if x_is_date and y_numeric:
            return "line"
        if x_numeric and y_numeric:
            return "scatter"
        if not x_numeric and y_numeric:
            return "bar"
        return "bar"

    def generate_chart_data(self, x_col: str, y_col: str | None, chart_type: str) -> dict:
        """Generate Recharts-compatible data payload."""
        df = self.df.copy()

        x_label = x_col.replace("_", " ").title()
        y_label = y_col.replace("_", " ").title() if y_col else "Count"

        if chart_type == "pie" or not y_col:
            counts = df[x_col].value_counts().head(20)
            data = [{"name": str(k), "value": int(v)} for k, v in counts.items()]
            title = f"Distribution of {x_label}"
            return {"data": data, "xLabel": x_label, "yLabel": "Count", "title": title}

        x_is_numeric = pd.to_numeric(df[x_col], errors="coerce").notna().mean() >= 0.8

        if chart_type == "scatter":
            df["_x"] = pd.to_numeric(df[x_col], errors="coerce")
            df["_y"] = pd.to_numeric(df[y_col], errors="coerce")
            subset = df[["_x", "_y"]].dropna()
            data = [{"x": round(float(r["_x"]), 4), "y": round(float(r["_y"]), 4)}
                    for _, r in subset.iterrows()]
            title = f"{y_label} vs {x_label}"
        elif chart_type == "line":
            # Aggregate by x (sorted)
            df["_y_num"] = pd.to_numeric(df[y_col], errors="coerce")
            grouped = df.groupby(x_col)["_y_num"].sum().reset_index()
            grouped = grouped.sort_values(x_col)
            data = [{"x": str(r[x_col]), "y": round(float(r["_y_num"]), 4)}
                    for _, r in grouped.iterrows()]
            title = f"{y_label} over {x_label}"
        else:
            # bar — aggregate categorical x
            df["_y_num"] = pd.to_numeric(df[y_col], errors="coerce")
            if x_is_numeric:
                # Scatter-like but still a bar
                data = [{"x": str(r[x_col]), "y": round(float(r["_y_num"]), 4) if pd.notna(r["_y_num"]) else 0}
                        for _, r in df[[x_col, "_y_num"]].dropna().iterrows()]
                data = data[:50]
            else:
                grouped = df.groupby(x_col)["_y_num"].sum().reset_index()
                data = [{"x": str(r[x_col]), "y": round(float(r["_y_num"]), 4)}
                        for _, r in grouped.iterrows()]
            title = f"{y_label} by {x_label}"

        return {"data": data, "xLabel": x_label, "yLabel": y_label, "title": title}

    def generate_correlation_heatmap(self) -> dict:
        """Return correlation matrix for all numeric columns."""
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return {"matrix": [], "columns": []}

        corr = numeric_df.corr()
        columns = corr.columns.tolist()
        matrix = [[round(float(v), 4) for v in row] for row in corr.values]
        return {"matrix": matrix, "columns": columns}
