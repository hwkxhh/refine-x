"""
RefineX End-to-End API Test
Runs every route in order: register → login → upload → poll →
cleaning → ai-analysis → charts → insights → comparison → health
"""

import time
import sys
import json
import requests

BASE = "http://localhost:8000"
CSV_PATH = r"D:\Program Files\Desktop\Refinex\bank-full.csv"

PASS = "\033[92m[OK]\033[0m"
FAIL = "\033[91m[ERR]\033[0m"
INFO = "\033[94m>>\033[0m"

errors: list[str] = []
token: str = ""
job_id: int = 0
chart_id: int = 0
insight_id: int = 0
job_id_2: int = 0   # second upload for comparison


def hdr():
    return {"Authorization": f"Bearer {token}"}


def check(label: str, resp: requests.Response, expected: int):
    if resp.status_code == expected:
        print(f"  {PASS}  {label}  [{resp.status_code}]")
        return True
    else:
        msg = f"{label} — expected {expected}, got {resp.status_code}: {resp.text[:200]}"
        print(f"  {FAIL}  {msg}")
        errors.append(msg)
        return False


# ──────────────────────────────────────────────────────────────────────────────
# 0. Health
# ──────────────────────────────────────────────────────────────────────────────
def test_health():
    print(f"\n{INFO} [0] HEALTH")
    r = requests.get(f"{BASE}/health")
    check("GET /health", r, 200)
    data = r.json()
    svcs = data.get('services', data)  # fallback if flat
    print(f"      DB={svcs.get('database')}  Redis={svcs.get('redis')}  Celery={svcs.get('celery')}")


# ──────────────────────────────────────────────────────────────────────────────
# 1. Auth
# ──────────────────────────────────────────────────────────────────────────────
def test_auth():
    global token
    print(f"\n{INFO} [1] AUTH")

    # Register (may already exist — 400 is acceptable)
    r = requests.post(f"{BASE}/auth/register", json={
        "name": "Test User", "email": "test@refinex.io", "password": "testpass123"
    })
    if r.status_code in (200, 201):
        print(f"  {PASS}  POST /auth/register  [{r.status_code}]")
    elif r.status_code in (400, 409) and ("already" in r.text.lower() or "registered" in r.text.lower()):
        print(f"  {PASS}  POST /auth/register  [{r.status_code} — user already exists, OK]")
    else:
        msg = f"POST /auth/register — unexpected {r.status_code}: {r.text[:200]}"
        print(f"  {FAIL}  {msg}")
        errors.append(msg)

    # Login
    r = requests.post(f"{BASE}/auth/login",
        data={"username": "test@refinex.io", "password": "testpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    if check("POST /auth/login", r, 200):
        token = r.json()["access_token"]

    # Me
    r = requests.get(f"{BASE}/auth/me", headers=hdr())
    check("GET /auth/me", r, 200)
    if r.status_code == 200:
        print(f"      User: {r.json()}")


# ──────────────────────────────────────────────────────────────────────────────
# 2. Upload
# ──────────────────────────────────────────────────────────────────────────────
def test_upload():
    global job_id
    print(f"\n{INFO} [2] UPLOAD")

    with open(CSV_PATH, "rb") as f:
        r = requests.post(f"{BASE}/upload",
            headers=hdr(),
            files={"file": ("bank-full.csv", f, "text/csv")})

    if check("POST /upload", r, 201):
        job_id = r.json()["id"]
        print(f"      Job ID: {job_id}  status={r.json()['status']}")

    # List jobs
    r = requests.get(f"{BASE}/upload/jobs", headers=hdr())
    check("GET /upload/jobs", r, 200)

    # Get job
    r = requests.get(f"{BASE}/upload/jobs/{job_id}", headers=hdr())
    check(f"GET /upload/jobs/{job_id}", r, 200)

    # Status
    r = requests.get(f"{BASE}/upload/jobs/{job_id}/status", headers=hdr())
    check(f"GET /upload/jobs/{job_id}/status", r, 200)


# ──────────────────────────────────────────────────────────────────────────────
# 3. Poll until pipeline completes (max 120 s)
# ──────────────────────────────────────────────────────────────────────────────
def poll_until_done():
    print(f"\n{INFO} [3] WAITING FOR PIPELINE  (job {job_id})")
    for i in range(120):
        r = requests.get(f"{BASE}/upload/jobs/{job_id}/status", headers=hdr())
        if r.status_code != 200:
            print(f"  {FAIL}  Poll failed: {r.text[:100]}")
            break
        data = r.json()
        status = data["status"]
        print(f"      [{i*2:>3}s] status={status}")

        if status == "awaiting_review":
            print(f"      Column review required — confirming all columns …")
            # Get the column_relevance_result to pick columns
            job_r = requests.get(f"{BASE}/upload/jobs/{job_id}", headers=hdr())
            cols_result = job_r.json().get("column_relevance_result") or {}
            confirmed = cols_result.get("all_columns", [])
            if not confirmed:
                # columns is a list of {"column": "name", ...} objects
                raw_cols = cols_result.get("columns") or []
                if isinstance(raw_cols, list):
                    confirmed = [
                        c.get("column") or c.get("name")
                        for c in raw_cols
                        if isinstance(c, dict) and ("column" in c or "name" in c)
                    ]
                elif isinstance(raw_cols, dict):
                    confirmed = list(raw_cols.keys())
            if not confirmed:
                # Last fallback — read the CSV header ourselves
                import csv
                with open(CSV_PATH, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    confirmed = next(reader)
            print(f"      Confirming columns: {confirmed[:5]}… ({len(confirmed)} total)")
            rev = requests.post(f"{BASE}/upload/jobs/{job_id}/review",
                headers={**hdr(), "Content-Type": "application/json"},
                json={"confirmed_columns": confirmed})
            if rev.status_code == 200:
                print(f"  {PASS}  POST /upload/jobs/{job_id}/review  [200]")
            else:
                msg = f"POST /upload/jobs/{job_id}/review — {rev.status_code}: {rev.text[:200]}"
                print(f"  {FAIL}  {msg}")
                errors.append(msg)
            time.sleep(4)
            continue

        if status == "completed":
            print(f"  {PASS}  Pipeline completed!")
            return True
        if status == "failed":
            msg = f"Pipeline FAILED: {data.get('error_message')}"
            print(f"  {FAIL}  {msg}")
            errors.append(msg)
            return False
        time.sleep(2)

    print(f"  {FAIL}  Pipeline did not complete within 120s")
    errors.append("Pipeline timeout")
    return False


# ──────────────────────────────────────────────────────────────────────────────
# 4. Cleaning routes
# ──────────────────────────────────────────────────────────────────────────────
def test_cleaning():
    print(f"\n{INFO} [4] CLEANING  (job {job_id})")

    r = requests.get(f"{BASE}/jobs/{job_id}/cleaning-summary", headers=hdr())
    check(f"GET /jobs/{job_id}/cleaning-summary", r, 200)
    if r.status_code == 200:
        d = r.json()
        print(f"      rows {d['row_count_original']}→{d['row_count_cleaned']}  quality={d['quality_score']}")

    r = requests.get(f"{BASE}/jobs/{job_id}/audit-trail", headers=hdr())
    check(f"GET /jobs/{job_id}/audit-trail", r, 200)
    if r.status_code == 200:
        print(f"      {len(r.json())} audit entries")

    r = requests.get(f"{BASE}/jobs/{job_id}/missing-fields", headers=hdr())
    check(f"GET /jobs/{job_id}/missing-fields", r, 200)

    r = requests.get(f"{BASE}/jobs/{job_id}/outliers", headers=hdr())
    check(f"GET /jobs/{job_id}/outliers", r, 200)

    r = requests.get(f"{BASE}/jobs/{job_id}/export", headers=hdr())
    check(f"GET /jobs/{job_id}/export", r, 200)
    if r.status_code == 200:
        print(f"      Download size: {len(r.content):,} bytes")


# ──────────────────────────────────────────────────────────────────────────────
# 5. AI Analysis
# ──────────────────────────────────────────────────────────────────────────────
def test_ai_analysis():
    print(f"\n{INFO} [5] AI ANALYSIS  (job {job_id})")

    r = requests.get(f"{BASE}/jobs/{job_id}/analyze-headers", headers=hdr())
    check(f"GET /jobs/{job_id}/analyze-headers", r, 200)
    if r.status_code == 200:
        d = r.json()
        print(f"      essential={len(d.get('essential_columns',[]))}  unnecessary={len(d.get('unnecessary_columns',[]))}")
        print(f"      summary: {d.get('dataset_summary','')[:80]}")

    # Drop zero columns (empty list = keep all)
    r = requests.post(f"{BASE}/jobs/{job_id}/drop-columns",
        headers={**hdr(), "Content-Type": "application/json"},
        json={"columns": []})
    check(f"POST /jobs/{job_id}/drop-columns (keep all)", r, 200)

    r = requests.get(f"{BASE}/jobs/{job_id}/formula-suggestions", headers=hdr())
    check(f"GET /jobs/{job_id}/formula-suggestions", r, 200)
    if r.status_code == 200:
        print(f"      {len(r.json().get('suggestions', []))} formula suggestions")


# ──────────────────────────────────────────────────────────────────────────────
# 6. Charts
# ──────────────────────────────────────────────────────────────────────────────
def test_charts():
    global chart_id
    print(f"\n{INFO} [6] CHARTS  (job {job_id})")

    # Set goal
    r = requests.post(f"{BASE}/jobs/{job_id}/goal",
        headers={**hdr(), "Content-Type": "application/json"},
        json={"goal_text": "Understand customer demographics and balance distribution", "goal_category": "analysis"})
    check(f"POST /jobs/{job_id}/goal", r, 200)

    # Get goal
    r = requests.get(f"{BASE}/jobs/{job_id}/goal", headers=hdr())
    check(f"GET /jobs/{job_id}/goal", r, 200)

    # Recommendations
    r = requests.get(f"{BASE}/jobs/{job_id}/recommendations", headers=hdr())
    check(f"GET /jobs/{job_id}/recommendations", r, 200)
    if r.status_code == 200:
        print(f"      {len(r.json())} AI chart recommendations")

    # Find valid columns from cleaning summary
    cs = requests.get(f"{BASE}/jobs/{job_id}/cleaning-summary", headers=hdr()).json()
    meta = cs.get("column_metadata") or {}
    cols = list(meta.keys()) if meta else []
    # Pick a numeric col for y, categorical for x
    x_col = cols[0] if cols else "age"
    y_col = cols[1] if len(cols) > 1 else None
    print(f"      Generating bar chart: x={x_col} y={y_col}")

    r = requests.post(f"{BASE}/jobs/{job_id}/charts",
        headers={**hdr(), "Content-Type": "application/json"},
        json={"chart_type": "bar", "x_col": x_col, "y_col": y_col, "title": "Test Chart"})
    if check(f"POST /jobs/{job_id}/charts", r, 201):
        chart_id = r.json()["id"]
        print(f"      Chart ID: {chart_id}")

    # List charts
    r = requests.get(f"{BASE}/jobs/{job_id}/charts", headers=hdr())
    check(f"GET /jobs/{job_id}/charts", r, 200)
    if r.status_code == 200:
        print(f"      {len(r.json())} chart(s)")

    # Get single chart
    if chart_id:
        r = requests.get(f"{BASE}/jobs/{job_id}/charts/{chart_id}", headers=hdr())
        check(f"GET /jobs/{job_id}/charts/{chart_id}", r, 200)


# ──────────────────────────────────────────────────────────────────────────────
# 7. Insights
# ──────────────────────────────────────────────────────────────────────────────
def test_insights():
    global insight_id
    print(f"\n{INFO} [7] INSIGHTS  (chart {chart_id})")

    if not chart_id:
        print(f"  {INFO}  Skipping — no chart_id available")
        return

    # Generate insight
    r = requests.post(f"{BASE}/charts/{chart_id}/insights", headers=hdr())
    if check(f"POST /charts/{chart_id}/insights", r, 201):
        insight_id = r.json()["id"]
        print(f"      Insight ID: {insight_id}  confidence={r.json().get('confidence')}")

    # List insights for job
    r = requests.get(f"{BASE}/jobs/{job_id}/insights", headers=hdr())
    check(f"GET /jobs/{job_id}/insights", r, 200)
    if r.status_code == 200:
        print(f"      {len(r.json())} insight(s)")

    # Get single insight
    if insight_id:
        r = requests.get(f"{BASE}/insights/{insight_id}", headers=hdr())
        check(f"GET /insights/{insight_id}", r, 200)


# ──────────────────────────────────────────────────────────────────────────────
# 8. Comparison (upload a second file, then compare)
# ──────────────────────────────────────────────────────────────────────────────
def test_comparison():
    global job_id_2
    print(f"\n{INFO} [8] COMPARISON")

    # Upload same file again as job 2
    with open(CSV_PATH, "rb") as f:
        r = requests.post(f"{BASE}/upload",
            headers=hdr(),
            files={"file": ("bank-full-v2.csv", f, "text/csv")})
    if not check("POST /upload (2nd file)", r, 201):
        return
    job_id_2 = r.json()["id"]
    print(f"      Job 2 ID: {job_id_2} — polling …")

    # Poll until done
    for i in range(120):
        r2 = requests.get(f"{BASE}/upload/jobs/{job_id_2}/status", headers=hdr())
        status = r2.json()["status"]
        if status == "awaiting_review":
            import csv
            with open(CSV_PATH, newline='', encoding='utf-8') as f:
                confirmed = next(csv.reader(f))
            requests.post(f"{BASE}/upload/jobs/{job_id_2}/review",
                headers={**hdr(), "Content-Type": "application/json"},
                json={"confirmed_columns": confirmed})
            time.sleep(4)
            continue
        if status == "completed":
            print(f"  {PASS}  Job 2 pipeline completed")
            break
        if status == "failed":
            print(f"  {FAIL}  Job 2 pipeline failed: {r2.json().get('error_message')}")
            errors.append("Job 2 pipeline failed")
            return
        time.sleep(2)
    else:
        errors.append("Job 2 pipeline timeout")
        return

    # Create comparison
    r = requests.post(f"{BASE}/compare",
        headers={**hdr(), "Content-Type": "application/json"},
        json={"job_id_1": job_id, "job_id_2": job_id_2})
    if check("POST /compare", r, 201):
        comp_id = r.json()["id"]
        mapping = r.json().get("header_mapping", {}).get("mapping", {})
        print(f"      Comparison ID: {comp_id}  mapped {len(mapping)} columns")

        # Confirm mapping
        r2 = requests.post(f"{BASE}/compare/{comp_id}/confirm-mapping",
            headers={**hdr(), "Content-Type": "application/json"},
            json={"mapping": mapping})
        check(f"POST /compare/{comp_id}/confirm-mapping", r2, 200)

        # Get deltas
        r3 = requests.get(f"{BASE}/compare/{comp_id}/deltas", headers=hdr())
        check(f"GET /compare/{comp_id}/deltas", r3, 200)

        # Comparison insight
        r4 = requests.post(f"{BASE}/compare/{comp_id}/insights", headers=hdr())
        check(f"POST /compare/{comp_id}/insights", r4, 200)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  RefineX End-to-End Test")
    print("=" * 60)

    test_health()
    test_auth()

    if not token:
        print(f"\n{FAIL}  Cannot continue — no auth token")
        sys.exit(1)

    test_upload()

    if not job_id:
        print(f"\n{FAIL}  Cannot continue — no job_id")
        sys.exit(1)

    completed = poll_until_done()
    if completed:
        test_cleaning()
        test_ai_analysis()
        test_charts()
        test_insights()
        test_comparison()

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if errors:
        print(f"  \033[91mFAILED — {len(errors)} error(s):\033[0m")
        for i, e in enumerate(errors, 1):
            print(f"    {i}. {e}")
        sys.exit(1)
    else:
        print(f"  \033[92mALL TESTS PASSED\033[0m")
        sys.exit(0)
