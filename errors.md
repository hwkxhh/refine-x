# RefineX — Known Errors & Root Causes

> Generated: March 2, 2026  
> Scope: All errors encountered or latent across the full cleaning pipeline.  
> Files referenced are relative to `refine-x/backend/`

---

## Summary Table

| # | Error | File | Status | Trigger |
|---|-------|------|--------|---------|
| 1 | VER-01 writes `"v0.0"` into int64 | `app/services/org_product_rules.py` | ✅ Fixed | Int col classified as HTYPE-047 |
| 2 | `run_trend_analysis` arithmetic on strings | `app/services/analytical_formulas.py` | ✅ Fixed | Object-dtype col in `numeric_cols` |
| 3 | `calculate_percentile` multiply string | `app/services/analytical_formulas.py` | ✅ Fixed | Object-dtype col in `numeric_cols` |
| 4 | `run_forecast` arithmetic on strings | `app/services/analytical_formulas.py` | ✅ Fixed | Object-dtype col in `numeric_cols` |
| 5 | `run_concentration_analysis` `v > 0` on strings | `app/services/analytical_formulas.py` | ❌ Open | No float guard, no `.dropna()` |
| 6 | `run_forecast` no float-cast guard | `app/services/analytical_formulas.py` | ❌ Open | Root cause fix is the only protection |
| 7 | VER-03 creates phantom `_sort_key` string column | `app/services/org_product_rules.py` | ❌ Open | Int col classified as HTYPE-047 |
| 8 | `detect_numeric_columns` wrong HTYPE codes | `app/services/analytical_formulas.py` | ❌ Open | Any file — silent wrong behavior |
| 9 | `detect_date_column` wrong HTYPE codes | `app/services/analytical_formulas.py` | ❌ Open | Any file — time-series analysis blind |
| 10 | `detect_and_bucket_ages` buckets non-age numerics | `app/services/cleaning.py` | ❌ Open | Any 0–120 range numeric column |
| 11 | `detect_and_convert_dates` converts non-date strings | `app/services/cleaning.py` | ❌ Open | Any string col where 80%+ parse as date |
| 12 | Non-UTF-8 encoding → `UnicodeDecodeError` | `app/tasks/process_csv.py` | ❌ Open | Latin-1 / Windows-1252 files |
| 13 | Non-comma delimiter → single-column parse | `app/tasks/process_csv.py` | ❌ Open | `;`, `\t`, `\|` separated files |
| 14 | Fuzzy dedup OOM on large files | `app/services/duplicate_resolution.py` | ❌ Open | Files with > 50k rows |
| 15 | `np.inf` in `col_meta` breaks JSON persistence | `app/tasks/process_csv.py` | ❌ Open | Any column containing infinity values |
| 16 | Quality score divide-by-zero | `app/services/quality.py` | ❌ Open | Empty file or all rows removed |
| 17 | No header row → first data row used as headers | `app/tasks/process_csv.py` | ❌ Open | Headerless CSV files |
| 18 | Excel multi-sheet silent data loss | `app/tasks/process_csv.py` | ❌ Open | `.xlsx` with data on sheet 2+ |
| 19 | VER-02 flags all integers as valid versions | `app/services/org_product_rules.py` | ❌ Open | Int col classified as HTYPE-047 |
| 20 | `run_goal_analysis` crashes on string column | `app/services/analytical_formulas.py` | ❌ Open | Target col with non-numeric dtype |

---

## Group 1 — Already Fixed (Jobs 12–16)

---

### Error 1 — VER-01 writes `"v0.0"` into int64 column

- **File:** `app/services/org_product_rules.py` → `VER_01_format_standardization`
- **Trigger:** Any column classified as HTYPE-047 (Version/Revision Number) whose actual pandas dtype is `int64` or `float64` (e.g. the `previous` column in `bank-full.csv`)
- **What breaks:** `normalize_version(str(0))` returns `"v0.0"` → `self.df.at[idx, col] = "v0.0"` into an int64 column → `TypeError: Invalid value 'v0.0' for dtype 'int64'` → entire Celery task crashes, job status = `failed`
- **Fix applied:** Added dtype guard at the top of the function — `if self.df[col].dtype.kind in ("i", "f"): return result`

---

### Error 2 — `run_trend_analysis` arithmetic on object-dtype column

- **File:** `app/services/analytical_formulas.py` → `run_trend_analysis`
- **Trigger:** `self.numeric_cols` contained a column that had been upcast to `object` dtype by VER-01 (before the fix), so `self.df[col].dropna().tolist()` returns a list mixing `int` and `str` values
- **What breaks:** `calculate_mean([1, "v0.0", 2])` inside `linear_regression` → `TypeError: unsupported operand type(s) for +: 'int' and 'str'`
- **Fix applied:** `try: values = [float(v) for v in values]` guard before the loop body + root-cause `__init__` dtype filter

---

### Error 3 — `calculate_percentile` multiply string

- **File:** `app/services/analytical_formulas.py` → `calculate_percentile` (called by `run_distribution_analysis`)
- **Trigger:** Same object-dtype column reaching percentile math
- **What breaks:** `sorted_vals[f] * (c - k)` where `sorted_vals` contains strings → `TypeError: can't multiply sequence by non-int of type 'float'`
- **Fix applied:** `sorted_vals = sorted(float(v) for v in values if v is not None)` wrapped in `try/except (TypeError, ValueError): return 0.0`

---

### Error 4 — `run_forecast` arithmetic on object-dtype column

- **File:** `app/services/analytical_formulas.py` → `run_forecast` → `an_17_simple_forecast` → `linear_regression` → `calculate_mean`
- **Trigger:** Same root cause as Errors 2 & 3 — `self.numeric_cols` included an object-dtype column
- **What breaks:** Same `TypeError: unsupported operand type(s) for +: 'int' and 'str'`
- **Fix applied (root cause):** `__init__` now filters `self.numeric_cols` by actual dtype — `[c for c in _raw_numeric if c in df.columns and df[c].dtype.kind in ("i", "f", "u")]`

---

## Group 2 — Unfixed Bugs (Hit With Any File)

---

### Error 5 — `run_concentration_analysis` — `v > 0` comparison on non-numeric values

- **File:** `app/services/analytical_formulas.py` → `run_concentration_analysis` → `an_18_concentration_index`
- **Trigger:** `values = self.df[col].tolist()` — no `.dropna()`, no float cast — then `[v for v in values if not pd.isna(v) and v > 0]` — the `v > 0` raises `TypeError` if `v` is a string
- **What breaks:** `TypeError: '>' not supported between instances of 'str' and 'int'` → job fails
- **Fix needed:** Add `.dropna()` and float-cast guard in `run_concentration_analysis` and inside `an_18_concentration_index`

---

### Error 6 — `run_forecast` has no float-cast guard

- **File:** `app/services/analytical_formulas.py` → `run_forecast`
- **Trigger:** `values = self.df[col].dropna().tolist()` feeds directly into `an_17_simple_forecast` with no `try: [float(v) for v in values]` guard — unlike `run_trend_analysis` and `run_distribution_analysis` which were patched
- **What breaks:** If the root-cause `__init__` dtype filter is ever bypassed or removed, crashes same as Error 4
- **Fix needed:** Add the same float-cast guard used in `run_trend_analysis`

---

### Error 7 — VER-03 creates phantom `_sort_key` string column from integer column

- **File:** `app/services/org_product_rules.py` → `VER_03_chronological_sort_key`
- **Trigger:** Any HTYPE-047 column with actual integer dtype (e.g. `previous`)
- **What breaks:** Creates `previous_sort_key` column filled with strings like `"0.0.0"` — corrupts the cleaned DataFrame with phantom columns that appear in `col_meta`, in the exported CSV, and in analytics column listings. No dtype guard.
- **Fix needed:** Add same guard as VER-01 — `if self.df[col].dtype.kind in ("i", "f"): return result`

---

### Error 8 — `detect_numeric_columns` uses completely wrong HTYPE codes

- **File:** `app/services/analytical_formulas.py` → `detect_numeric_columns`
- **The bug:** The `elif` branch checks `htype_map[col] in ["HTYPE-019", "HTYPE-020", "HTYPE-021", "HTYPE-022", "HTYPE-023", "HTYPE-024", "HTYPE-025"]` — but those HTYPEs are: Category (019), Status (020), Score (021), Text/Notes (022), URL (023), Product Name (024), SKU/Barcode (025). None are numeric.
- **Correct numeric HTYPEs:** HTYPE-015 (Amount/Currency), HTYPE-016 (Quantity), HTYPE-017 (Percentage), HTYPE-042 (Currency Code), HTYPE-043 (Rank), HTYPE-044 (Calculated/Derived)
- **What breaks:** String/category columns are added to `_raw_numeric` list. The `__init__` dtype filter accidentally masks this — but the bug still pollutes the detection logic and will cause silent failures if the dtype filter is removed.
- **Fix needed:** Replace the wrong HTYPE codes with `["HTYPE-015", "HTYPE-016", "HTYPE-017", "HTYPE-042", "HTYPE-043", "HTYPE-044"]`

---

### Error 9 — `detect_date_column` uses completely wrong HTYPE codes

- **File:** `app/services/analytical_formulas.py` → `detect_date_column`
- **The bug:** Checks `htype in ["HTYPE-013", "HTYPE-014", "HTYPE-015"]` as date types — those are Country (013), Postal Code (014), and Numeric Amount (015). Not dates.
- **Correct date HTYPEs:** HTYPE-004 (Date), HTYPE-005 (Time), HTYPE-006 (DateTime Combined)
- **What breaks:** HTYPE-based date detection never fires. Time-series analysis (AN-01 through AN-05, AN-09, AN-10, AN-11) only accidentally works if the date column name contains `"date"`, `"time"`, `"timestamp"`, `"created"`, `"updated"`, or `"period"`. Any date column with an unusual name is completely invisible to all time-series analytics.
- **Fix needed:** Replace the wrong HTYPE codes with `["HTYPE-004", "HTYPE-005", "HTYPE-006"]`

---

### Error 19 — VER-02 silently flags all integers as valid parsed versions

- **File:** `app/services/org_product_rules.py` → `VER_02_semantic_version_parsing`
- **Trigger:** HTYPE-047 column that is actually integer (e.g. `previous` with values `0`, `1`, `2`)
- **What breaks:** The `^v?(\d+)$` regex matches bare integers → all rows reported as `"parsed"` versions with `format="major_only"` → audit trail is polluted with meaningless version-parsing logs → `details["formats_detected"]` reports `["major_only"]` as if this is a real version column. No dtype guard.
- **Fix needed:** Add same guard as VER-01 — `if self.df[col].dtype.kind in ("i", "f"): return result`

---

## Group 3 — Will Hit With Different File Types / Larger Files

---

### Error 10 — `detect_and_bucket_ages` incorrectly converts non-age numeric columns

- **File:** `app/services/cleaning.py` → `detect_and_bucket_ages`
- **Trigger:** Any numeric column where ≥90% of values fall in the range 0–120 AND max ≤ 120 — this matches `score`, `rating`, `percentage`, `satisfaction`, `campaign_count`, `pdays`, etc.
- **What breaks:** Column silently converted from int64 to object strings `"0-18"`, `"19-35"`, `"36-60"`, `"60+"`. Data semantics permanently corrupted. Analytics skips the column. Exported CSV has age-bucket strings in what was a score or count column.
- **Fix needed:** Require column name to contain an age keyword (`age`, `years`, `dob`, `birth`) before bucketizing — not just the numeric range

---

### Error 11 — `detect_and_convert_dates` converts non-date string columns

- **File:** `app/services/cleaning.py` → `detect_and_convert_dates`
- **Trigger:** Any string column where 80%+ of values are parseable as dates by `pd.to_datetime` — e.g. a `batch_year` column with `"2020"`, `"2021"`; an `id` column like `"2024-001"`; month names in any format
- **What breaks:** Column silently rewritten as `"YYYY-MM"` strings, original data destroyed, no way to recover
- **Fix needed:** Add name-based keyword guard (must contain `date`, `time`, `dob`, etc.) before attempting conversion

---

### Error 12 — Non-UTF-8 file encoding crashes at file read

- **File:** `app/tasks/process_csv.py` → `pd.read_csv(io.BytesIO(file_bytes))`
- **Trigger:** CSV files encoded in Latin-1, Windows-1252, or ISO-8859-1 — extremely common for data exported from European Excel installations
- **What breaks:** `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position N: invalid continuation byte` → job fails immediately before any cleaning runs
- **Fix needed:** Try UTF-8 first, fall back to `chardet` detection or explicit `encoding="latin-1"` on failure

---

### Error 13 — Non-comma delimiter parsed as single-column DataFrame

- **File:** `app/tasks/process_csv.py` → `pd.read_csv` with no `sep` parameter
- **Trigger:** European CSV (`;` delimiter), tab-delimited `.tsv`, or pipe `|` separated files
- **What breaks:** Entire file becomes one column with the full row as the column name (e.g. `"age;job;marital;education;..."`). Cleaning runs on this garbage structure, job "completes" with a 1-column dataset
- **Fix needed:** Use `pd.read_csv(..., sep=None, engine="python")` for auto-detection, or sniff the delimiter with `csv.Sniffer`

---

### Error 14 — Fuzzy deduplication OOM / timeout on large files

- **File:** `app/services/duplicate_resolution.py`
- **Trigger:** Files with more than ~50,000 rows
- **What breaks:** Fuzzy matching is O(n²) — pairwise comparison of all rows. At 100k rows this is 10 billion comparisons. Worker process runs out of memory or hits Celery task timeout. Job fails.
- **Fix needed:** Cap fuzzy dedup at a configurable max row count (e.g. 10,000 rows), or switch to blocking/indexing strategies (e.g. block on first letter of a key column before fuzzy matching)

---

## Group 4 — Serialization & Persistence Errors

---

### Error 15 — `np.inf` in `col_meta["sample"]` breaks JSON persistence

- **File:** `app/tasks/process_csv.py` → building `col_meta`
- **The bug:** `series.dropna().head(3).tolist()` — `.dropna()` removes `NaN` but does NOT remove `np.inf` or `-np.inf`. JSON does not support infinity values.
- **What breaks:** `json.dumps({"sample": [float("inf"), 2.5, 3.0]})` → `ValueError: Out of range float values are not JSON compliant` → SQLAlchemy fails to persist `CleanedDataset` → job crashes at the very last step after all cleaning is done
- **Fix needed:** Replace `np.inf` and `-np.inf` with `None` in `col_meta` sample values before persistence

---

### Error 16 — Quality score divide-by-zero

- **File:** `app/services/quality.py` → `calculate_quality_score`
- **Trigger:** `original_row_count = 0` (uploaded empty file) OR all rows removed by duplicate resolution / empty column drops
- **What breaks:** Division by zero → `ZeroDivisionError` → job crashes at the final quality calculation step, after all cleaning has successfully completed
- **Fix needed:** Guard with `if original_row_count == 0: return 0.0` (or 100.0 depending on desired behavior)

---

## Group 5 — Structural / Format Edge Cases

---

### Error 17 — File with no header row

- **File:** `app/tasks/process_csv.py` → `pd.read_csv` with default `header=0`
- **Trigger:** CSVs that start directly with data rows (no column name row) — common in raw database dumps, IoT exports, legacy system outputs
- **What breaks:** First data row becomes column names (e.g. `"John"`, `"25"`, `"male"`). The rest of the data shifts up by one row. Cleaning runs on misaligned, mislabelled data and silently produces garbage output.
- **Fix needed:** Detect headerless files (e.g. all "column names" are numeric or match value patterns) and either auto-generate column names (`col_0`, `col_1`, ...) or flag for user confirmation via `struct_flags`

---

### Error 18 — Excel files with multiple sheets — silent data loss

- **File:** `app/tasks/process_csv.py` → `pd.read_excel` with no `sheet_name` parameter
- **Trigger:** Any `.xlsx` or `.xls` file where the meaningful data is on sheet 2, 3, or named sheets
- **What breaks:** `pd.read_excel` defaults to `sheet_name=0` — only the first sheet is read. All other sheets are silently ignored. User receives cleaned data from the wrong sheet with no warning.
- **Fix needed:** Read sheet names, detect which sheet has the most data, or expose sheet selection in the upload API. At minimum, log a warning in `struct_flags` listing all available sheet names.

---

### Error 20 — `run_goal_analysis` crashes on non-numeric target column

- **File:** `app/services/analytical_formulas.py` → `run_goal_analysis`
- **Trigger:** If `self.targets` dict is populated (via API) with a column name that has been upcast to `object` dtype by an upstream cleaning rule
- **What breaks:** `an_16_goal_vs_actual` → `clean_values = [v for v in actual_values if not pd.isna(v)]` → `sum(clean_values)` where `clean_values` contains strings → `TypeError: unsupported operand type(s) for +: 'int' and 'str'`
- **Fix needed:** Add float-cast guard in `an_16_goal_vs_actual`: `clean_values = [float(v) for v in actual_values if not pd.isna(v)]` wrapped in `try/except`

---

## Fix Priority

| Priority | Errors | Reason |
|----------|--------|--------|
| **P0 — Fix immediately** | 5, 6, 7, 8, 9, 19 | Will crash the current `bank-full.csv` job or corrupt output silently |
| **P1 — Fix before production** | 10, 11, 12, 13, 15, 16, 20 | Will crash or corrupt data with any slightly different file |
| **P2 — Fix before scale** | 14, 17, 18 | Edge cases / large-scale failures |
