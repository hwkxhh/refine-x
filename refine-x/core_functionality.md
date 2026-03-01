# RefineX — Step-by-Step Development Guideline

## 📍 Where You Are Now
✅ Authentication complete (login/signup working)  
✅ Docker services running  
✅ Database connected  
✅ Celery worker ready  

**Next Goal:** Build file upload system with background processing

---

## 🎯 PHASE 2: FILE UPLOAD & BACKGROUND PROCESSING

### Step 1: Create the Upload Job Database Model

**What:** Create a database table to track every file a user uploads

**Why:** You need to store metadata about uploaded files (filename, status, quality score, etc.)

**Do this:**
1. Create a new file: `app/models/upload_job.py`
2. Define a database model called `UploadJob` with these fields:
   - `id` (primary key)
   - `user_id` (foreign key to users table)
   - `filename` (string)
   - `file_path` (string - the MinIO/S3 path)
   - `file_size` (integer - bytes)
   - `file_type` (string - 'csv' or 'xlsx')
   - `status` (string - 'pending', 'processing', 'completed', 'failed')
   - `error_message` (string, nullable)
   - `row_count` (integer, nullable - filled after processing)
   - `column_count` (integer, nullable)
   - `quality_score` (float, nullable - 0 to 100)
   - `created_at` (datetime)
   - `processed_at` (datetime, nullable)
3. Add a relationship back to the User model
4. Save the file

**Next:** Update your User model

---

### Step 2: Update User Model for Relationship

**What:** Link users to their upload jobs

**Why:** So you can query "get all uploads for this user"

**Do this:**
1. Open `app/models/user.py`
2. Add a relationship field called `upload_jobs` that connects to the UploadJob model
3. Save the file

**Next:** Create database migration

---

### Step 3: Create and Apply Database Migration

**What:** Generate the SQL to create the upload_jobs table in PostgreSQL

**Why:** Database needs the new table structure

**Do this:**
1. Open terminal in `backend/` folder
2. Activate virtual environment
3. Run: `alembic revision --autogenerate -m "add upload_jobs table"`
4. Check the generated migration file in `alembic/versions/` - it should create the upload_jobs table
5. Run: `alembic upgrade head` to apply the migration
6. Verify: Open pgAdmin or database GUI, check that `upload_jobs` table exists with all columns

**Next:** Create Pydantic response schemas

---

### Step 4: Create Upload Response Schemas

**What:** Define what data your API will return when someone uploads a file or checks job status

**Why:** FastAPI uses these for validation and API documentation

**Do this:**
1. Create a new file: `app/schemas/upload.py`
2. Create these schema classes:
   - `UploadJobResponse` - full job details (all fields from the model)
   - `UploadJobListResponse` - simplified version for lists (id, filename, status, quality_score, created_at)
   - `JobStatusResponse` - for polling endpoint (job_id, status, progress percentage, quality_score, error_message)
3. Save the file

**Next:** Build the storage service

---

### Step 5: Create Storage Service for MinIO

**What:** Build a service that handles uploading, downloading, and deleting files from MinIO

**Why:** You need a clean interface to interact with file storage without repeating boto3 code everywhere

**Do this:**
1. Create a new file: `app/services/storage.py`
2. Create a class called `StorageService` with these methods:
   - `validate_file(file)` - checks if file type is CSV/Excel and size is under 50MB
   - `upload_file(file, job_id)` - uploads file to MinIO bucket, returns the S3 path
   - `download_file(file_path)` - downloads file from MinIO as bytes
   - `delete_file(file_path)` - removes file from MinIO
3. Initialize boto3 S3 client in the class __init__ using your MinIO credentials from .env
4. At the bottom of the file, create a singleton instance called `storage_service`
5. Save the file

**Technical details:**
- Use boto3.client('s3', endpoint_url=...) with MinIO endpoint
- File path format: `s3://refinex-uploads/uploads/{job_id}/{filename}`
- Validate: CSV/XLSX only, max 50MB
- Handle exceptions and raise HTTPException with clear error messages

**Next:** Create the Celery background task

---

### Step 6: Build Celery Task for CSV Processing

**What:** Create a background task that processes uploaded CSV files asynchronously

**Why:** Large files take time to process - you can't block the API request while reading and analyzing the file

**Do this:**
1. Open `app/tasks/process_csv.py`
2. Create a Celery task function called `process_csv_file(job_id)`
3. Task should do these steps in order:
   - Get the UploadJob from database using the job_id
   - Update job status to "processing"
   - Download the file from MinIO using storage_service
   - Load the file into a Pandas DataFrame (use pd.read_csv or pd.read_excel depending on file_type)
   - Count rows and columns
   - Calculate a simple quality score (completeness: % of non-null cells)
   - Update job with: status="completed", row_count, column_count, quality_score, processed_at timestamp
   - If anything fails, catch the exception and set status="failed" with error message
4. Decorate function with `@celery_app.task(bind=True)`
5. Save the file
6. Restart your Celery worker - check the terminal, you should see this new task listed

**Next:** Create the upload API endpoints

---

### Step 7: Build Upload API Routes

**What:** Create the FastAPI endpoints that handle file uploads and job management

**Why:** These are the HTTP endpoints your frontend will call

**Do this:**
1. Create a new file: `app/routes/upload.py`
2. Create an APIRouter with prefix="/upload"
3. Build these endpoint functions:

   **POST /upload**
   - Accept multipart/form-data with a file
   - Require JWT authentication (get current user)
   - Validate the file using storage_service.validate_file()
   - If invalid, return 400 error
   - Create an UploadJob record in database with status="pending"
   - Upload the file to MinIO using storage_service.upload_file()
   - Update the job record with the file_path
   - Queue the Celery task: process_csv_file.delay(job_id)
   - Return the UploadJob as response (immediately, don't wait for processing)

   **GET /upload/jobs**
   - Require JWT authentication
   - Query all UploadJobs for the current user
   - Order by created_at descending (newest first)
   - Return list of jobs

   **GET /upload/jobs/{job_id}**
   - Require JWT authentication
   - Get specific job by ID
   - Verify job belongs to current user (if not, return 404)
   - Return full job details

   **GET /upload/jobs/{job_id}/status**
   - Require JWT authentication
   - Get the job
   - Calculate progress percentage based on status (pending=0%, processing=50%, completed=100%)
   - Return job_id, status, progress, quality_score, row_count, error_message
   - This is the endpoint frontend will poll every 2-3 seconds

   **DELETE /upload/jobs/{job_id}**
   - Require JWT authentication
   - Get the job, verify ownership
   - Delete file from MinIO using storage_service.delete_file()
   - Delete job record from database
   - Return success message

4. Save the file

**Next:** Register the router in main.py

---

### Step 8: Register Upload Router in FastAPI App

**What:** Add your new upload routes to the main FastAPI application

**Why:** Routes won't work until they're registered with the app

**Do this:**
1. Open `app/main.py`
2. Import the upload router at the top: `from app.routes import upload`
3. Add the router: `app.include_router(upload.router)`
4. Save the file
5. Check your terminal - FastAPI should auto-reload
6. Open http://localhost:8000/docs - you should see the new /upload endpoints in Swagger UI

**Next:** Verify MinIO bucket exists

---

### Step 9: Create MinIO Bucket

**What:** Create the storage bucket where uploaded files will be stored

**Why:** boto3 will fail if the bucket doesn't exist

**Do this:**
1. Open browser: http://localhost:9001
2. Login: username `minioadmin`, password `minioadmin123`
3. Click "Buckets" in left sidebar
4. Click "Create Bucket" button
5. Enter bucket name: `refinex-uploads`
6. Click "Create"
7. Verify the bucket appears in the list

**Next:** Update your .env file

---

### Step 10: Verify Environment Variables

**What:** Make sure all MinIO/S3 settings are in your .env file

**Why:** Your storage service won't connect without these

**Do this:**
1. Open `backend/.env`
2. Verify these lines exist:
   ```
   S3_ENDPOINT=http://localhost:9000
   S3_ACCESS_KEY=minioadmin
   S3_SECRET_KEY=minioadmin123
   S3_BUCKET=refinex-uploads
   ```
3. If missing, add them
4. Save the file
5. Restart FastAPI (CTRL+C then `uvicorn app.main:app --reload` again)

**Next:** Test the complete flow

---

### Step 11: Test File Upload Flow

**What:** Test the entire upload → process → complete workflow

**Why:** Verify everything works end-to-end before building more features

**Do this:**

**11.1 Login to get JWT token**
1. Open Thunder Client (or Postman)
2. Create POST request to `http://localhost:8000/auth/login`
3. Body (JSON):
   ```json
   {
     "email": "your@email.com",
     "password": "yourpassword"
   }
   ```
4. Send request
5. Copy the `access_token` from response

**11.2 Upload a CSV file**
1. Create POST request to `http://localhost:8000/upload`
2. Headers: Add `Authorization: Bearer YOUR_ACCESS_TOKEN`
3. Body: Select "Form" type, add a field called "file" with type "File"
4. Choose a CSV file from your computer (any CSV, even a simple one with a few rows)
5. Send request
6. You should get a response with job_id and status="pending"
7. **Copy the job_id** (you'll need it)

**11.3 Check Celery worker**
1. Look at your Celery terminal
2. You should see log messages showing the task started and completed
3. If you see errors, read them carefully - they tell you what's wrong

**11.4 Poll job status**
1. Create GET request to `http://localhost:8000/upload/jobs/{job_id}/status`
2. Replace {job_id} with the ID from step 11.2
3. Headers: Add `Authorization: Bearer YOUR_ACCESS_TOKEN`
4. Send request
5. First time might show status="processing"
6. Wait 2-3 seconds, send again
7. Should show status="completed" with quality_score and row_count

**11.5 Verify in MinIO**
1. Go to http://localhost:9001
2. Click "Buckets" → "refinex-uploads"
3. Navigate to uploads/{job_id}/
4. You should see your uploaded file there

**11.6 Verify in database**
1. Open pgAdmin (or your database GUI)
2. Connect to refinex_db
3. Query: `SELECT * FROM upload_jobs ORDER BY created_at DESC LIMIT 5;`
4. You should see your upload with all fields filled (status, quality_score, row_count, etc.)

**11.7 Test list endpoint**
1. Create GET request to `http://localhost:8000/upload/jobs`
2. Headers: Add `Authorization: Bearer YOUR_ACCESS_TOKEN`
3. Send request
4. Should return array with your upload(s)

**11.8 Test delete endpoint**
1. Create DELETE request to `http://localhost:8000/upload/jobs/{job_id}`
2. Headers: Add `Authorization: Bearer YOUR_ACCESS_TOKEN`
3. Send request
4. Should return success message
5. Check MinIO - file should be gone
6. Check database - job record should be deleted

**Next:** Check completion checklist

---

### Step 12: Phase 2 Completion Checklist

**What:** Verify everything works before moving to Phase 3

**Why:** Building on a broken foundation leads to cascading problems

**Go through this checklist:**
- [ ] Can upload a CSV file and get job_id back immediately
- [ ] Can upload an Excel (.xlsx) file successfully
- [ ] Uploading a .txt file returns 400 error with clear message
- [ ] Uploading a 60MB file returns 400 error (over size limit)
- [ ] Celery worker shows task execution in terminal
- [ ] Job status changes from "pending" to "processing" to "completed"
- [ ] Quality score is calculated and stored
- [ ] Row count and column count are correct
- [ ] File appears in MinIO console at correct path
- [ ] Can get list of all my uploads
- [ ] Can get details of a specific upload
- [ ] Can poll job status endpoint repeatedly without errors
- [ ] Can delete an upload (removes from database AND MinIO)
- [ ] All endpoints reject requests without JWT token (401 error)
- [ ] Can't access another user's upload jobs (returns 404)

**If any checkbox fails:** Go back and debug that specific part. Don't continue until all pass.

**Next:** Move to Phase 3

---

## 🎯 PHASE 3: DATA CLEANING PIPELINE (Weeks 3-5)

### Overview
Now that files are uploading and processing, you'll build the actual data cleaning engine.

---

### Step 13: Create Cleaned Dataset Model

**What:** Create a table to store the results of cleaning (after the CSV is processed)

**Why:** You need to save the cleaned data metadata and quality metrics

**Do this:**
1. Create `app/models/cleaned_dataset.py`
2. Define model `CleanedDataset` with these fields:
   - `id` (primary key)
   - `job_id` (foreign key to upload_jobs, unique - one cleaned dataset per upload)
   - `column_metadata` (JSON field - stores info about each column: data type, null count, unique count)
   - `row_count_original` (integer)
   - `row_count_cleaned` (integer - after removing duplicates)
   - `quality_score` (float 0-100)
   - `cleaning_summary` (JSON - stores what was cleaned: duplicates_removed, outliers_flagged, etc.)
   - `created_at` (datetime)
3. Add relationship to UploadJob
4. Save file

**Next:** Create cleaning log model

---

### Step 14: Create Cleaning Log Model (Audit Trail)

**What:** Create a table to record every single change made to the data

**Why:** Users need transparency - they must see exactly what was changed and why

**Do this:**
1. Create `app/models/cleaning_log.py`
2. Define model `CleaningLog` with these fields:
   - `id` (primary key)
   - `job_id` (foreign key to upload_jobs)
   - `row_index` (integer, nullable - which row was affected)
   - `column_name` (string, nullable - which column)
   - `action` (string - 'remove_duplicate', 'fill_missing', 'flag_outlier', 'normalize_column_name', etc.)
   - `original_value` (string, nullable)
   - `new_value` (string, nullable)
   - `reason` (string - explanation of why this action was taken)
   - `timestamp` (datetime)
3. Add relationship to UploadJob
4. Save file

**Next:** Create migrations

---

### Step 15: Create Migrations for New Models

**What:** Generate SQL to create cleaned_datasets and cleaning_logs tables

**Do this:**
1. Terminal: `alembic revision --autogenerate -m "add cleaned_dataset and cleaning_log tables"`
2. Check generated migration file
3. Terminal: `alembic upgrade head`
4. Verify tables exist in database

**Next:** Build the cleaning pipeline service

---

### Step 16: Build Data Cleaning Service (Phase 1: Structural Cleanup)

**What:** Create a service that cleans CSV data in 4 phases. Start with Phase 1: structural cleanup.

**Why:** Raw CSV data is messy - duplicates, empty columns, inconsistent formatting

**Do this:**
1. Create `app/services/cleaning.py`
2. Create a class called `DataCleaningPipeline`
3. In __init__, accept: job_id, DataFrame, database session
4. Create method `remove_duplicates()`:
   - Use Pandas to detect duplicate rows
   - For each duplicate found, log it to cleaning_logs table
   - Remove duplicates from DataFrame
   - Return count of removed rows
5. Create method `normalize_column_names()`:
   - For each column name: strip whitespace, convert to lowercase, replace spaces with underscores
   - Log each rename to cleaning_logs
   - Update DataFrame column names
6. Create method `remove_empty_columns(threshold=0.8)`:
   - For each column, calculate % of null values
   - If >80% null, mark for removal
   - Log the removal
   - Drop those columns from DataFrame
   - Return count of removed columns
7. Save file

**Next:** Add Phase 2 cleaning methods

---

### Step 17: Build Data Cleaning Service (Phase 2: Value Standardization)

**What:** Add methods to standardize date formats and age buckets

**Why:** Inconsistent date formats ("01/15/2024" vs "2024-01-15") break charts

**Do this:**
1. Open `app/services/cleaning.py`
2. Add method `detect_and_convert_dates()`:
   - For each column, check if values look like dates (use regex or try pd.to_datetime)
   - If 80%+ of values are dates, convert entire column to YYYY-MM format
   - Log conversions
   - Return count of columns converted
3. Add method `detect_and_bucket_ages()`:
   - For each numeric column, check if values are in range 0-120
   - If yes, likely an age column
   - Create buckets: "0-18", "19-35", "36-60", "60+"
   - Replace values with bucket labels
   - Log conversions
   - Return count of columns bucketed
4. Save file

**Next:** Add Phase 3 cleaning methods

---

### Step 18: Build Data Cleaning Service (Phase 3: Missing Data Handling)

**What:** Add methods to detect and fill missing values

**Why:** Missing data breaks calculations and charts

**Do this:**
1. Open `app/services/cleaning.py`
2. Add method `identify_missing_values()`:
   - For each column, count null values
   - Calculate percentage
   - Return dictionary: `{column_name: {count: X, percentage: Y}}`
3. Add method `auto_fill_numeric(column, method='mean')`:
   - For numeric columns, fill nulls with mean (or median)
   - Log each fill with original row index
   - Return count filled
4. Add method `auto_fill_categorical(column, method='mode')`:
   - For text columns, fill nulls with most common value
   - Log each fill
   - Return count filled
5. Save file

**Next:** Add Phase 4 cleaning methods

---

### Step 19: Build Data Cleaning Service (Phase 4: Outlier Detection)

**What:** Add method to detect statistical outliers using IQR method

**Why:** Outliers can skew analysis - users need to know about them

**Do this:**
1. Open `app/services/cleaning.py`
2. Add method `detect_outliers_iqr(column)`:
   - Calculate Q1 (25th percentile), Q3 (75th percentile)
   - Calculate IQR = Q3 - Q1
   - Flag any value < Q1 - 1.5*IQR or > Q3 + 1.5*IQR as outlier
   - Don't remove them automatically - just flag
   - Log each outlier found
   - Return list of: `[{row_index, column, value, expected_range}]`
3. Save file

**Next:** Add quality score calculator

---

### Step 20: Build Quality Score Calculator

**What:** Create a function that calculates a 0-100 quality score for a dataset

**Why:** Users need one number to understand "how clean is my data"

**Do this:**
1. Create `app/services/quality.py`
2. Create function `calculate_quality_score(df, original_row_count)`:
3. Calculate 4 sub-scores:
   - **Completeness** (40% weight): `(total_cells - null_cells) / total_cells * 100`
   - **Uniqueness** (30% weight): `(total_rows - duplicate_rows) / total_rows * 100`
   - **Consistency** (20% weight): % of columns with uniform data types (all numeric, or all text)
   - **Integrity** (10% weight): Reduction from outlier removal/flagging
4. Combine: `(completeness*0.4 + uniqueness*0.3 + consistency*0.2 + integrity*0.1)`
5. Return final 0-100 score
6. Save file

**Next:** Add Redis caching

---

### Step 21: Add Redis Caching for Cleaned DataFrames

**What:** Store the cleaned DataFrame in Redis after processing

**Why:** Re-running Pandas operations on every API call is slow - cache the result

**Do this:**
1. Install Redis client if not already: `pip install redis`
2. Update `requirements.txt`
3. Create `app/services/cache.py`
4. Create function `cache_dataframe(job_id, df)`:
   - Convert DataFrame to JSON using `df.to_json()`
   - Store in Redis with key `cleaned_df:{job_id}`
   - Set expiration: 1 hour (3600 seconds)
5. Create function `get_cached_dataframe(job_id)`:
   - Get from Redis using key `cleaned_df:{job_id}`
   - If exists, convert back to DataFrame using `pd.read_json()`
   - If not exists, return None
6. Create function `delete_cached_dataframe(job_id)`:
   - Delete from Redis
7. Save file

**Next:** Update the Celery processing task

---

### Step 22: Update Celery Task to Run Cleaning Pipeline

**What:** Modify the `process_csv_file` task to run all cleaning phases

**Why:** Right now it only reads the CSV - it needs to actually clean it

**Do this:**
1. Open `app/tasks/process_csv.py`
2. After loading DataFrame, add these steps:
   - Initialize `DataCleaningPipeline(job_id, df, db)`
   - Run Phase 1: remove_duplicates(), normalize_column_names(), remove_empty_columns()
   - Run Phase 2: detect_and_convert_dates(), detect_and_bucket_ages()
   - Run Phase 3: identify_missing_values(), auto_fill_numeric() for each numeric column with nulls
   - Run Phase 4: detect_outliers_iqr() for each numeric column
   - Calculate quality score using the quality service
   - Create CleanedDataset record with all metadata
   - Save all cleaning logs to database
   - Cache cleaned DataFrame in Redis
   - Update UploadJob with final quality_score
3. Save file
4. Restart Celery worker

**Next:** Create cleaning API endpoints

---

### Step 23: Create Cleaning API Endpoints

**What:** Build API routes to let users view cleaning results

**Why:** Users need to see what was cleaned, review audit trail, export cleaned data

**Do this:**
1. Create `app/routes/cleaning.py`
2. Create APIRouter with prefix="/jobs"
3. Build these endpoints:

   **GET /jobs/{job_id}/cleaning-summary**
   - Get CleanedDataset record
   - Return: duplicates_removed, outliers_flagged, missing_values_filled, quality_score, row_count_before, row_count_after

   **GET /jobs/{job_id}/audit-trail**
   - Query all CleaningLog records for this job_id
   - Order by timestamp
   - Return list of all changes (action, column, old_value, new_value, reason, timestamp)
   - Add pagination if >100 logs (limit/offset)

   **GET /jobs/{job_id}/missing-fields**
   - Get cached DataFrame from Redis
   - Run identify_missing_values()
   - Return: `{column: {count, percentage}}` for columns with nulls

   **POST /jobs/{job_id}/fill-missing**
   - Accept: `{column, row_indices, values}` in request body
   - Get cached DataFrame
   - Fill specified cells with provided values
   - Log the manual fills to cleaning_logs
   - Update cached DataFrame in Redis
   - Return success

   **GET /jobs/{job_id}/outliers**
   - Get all CleaningLog records where action='flag_outlier'
   - Return: `[{row_index, column, value, expected_range}]`

   **POST /jobs/{job_id}/resolve-outlier**
   - Accept: `{row_index, action: 'keep' | 'remove'}`
   - Get cached DataFrame
   - If 'remove': drop that row
   - Log the decision
   - Update cached DataFrame
   - Return success

   **GET /jobs/{job_id}/export**
   - Get cached DataFrame from Redis
   - Convert to CSV using `df.to_csv()`
   - Return as file download (StreamingResponse with media_type='text/csv')

4. Save file
5. Register router in `main.py`
6. Check Swagger docs for new endpoints

**Next:** Test cleaning pipeline

---

### Step 24: Test Data Cleaning Pipeline

**What:** Upload a messy CSV and verify all cleaning phases work

**Do this:**

**24.1 Create a test CSV**
1. Create a CSV file with intentional problems:
   - Duplicate rows (same data repeated)
   - Missing values (empty cells)
   - Inconsistent date formats ("1/15/2024" and "2024-01-15" in same column)
   - An age column (numeric 0-100)
   - Some outliers (like age=999)
   - Column names with spaces and capitals ("Student Name", "Test Score")
2. Save as `test_data_messy.csv`

**24.2 Upload the file**
1. POST to /upload with your messy CSV
2. Get job_id

**24.3 Wait for processing**
1. Poll /upload/jobs/{job_id}/status
2. Wait until status="completed"
3. Note the quality_score

**24.4 Check cleaning summary**
1. GET /jobs/{job_id}/cleaning-summary
2. Verify it shows:
   - Number of duplicates removed
   - Number of outliers flagged
   - Number of missing values filled
   - Before/after row counts

**24.5 Check audit trail**
1. GET /jobs/{job_id}/audit-trail
2. Verify you see entries for:
   - Duplicate removals (with row indices)
   - Column renames (original → new)
   - Date conversions
   - Age bucketing
   - Missing value fills
   - Outlier flags

**24.6 Check missing fields**
1. GET /jobs/{job_id}/missing-fields
2. Should show any remaining columns with nulls

**24.7 Export cleaned CSV**
1. GET /jobs/{job_id}/export
2. Download the file
3. Open in Excel/Google Sheets
4. Verify:
   - Duplicates are gone
   - Column names are normalized (lowercase, underscores)
   - Dates are in consistent format
   - Ages are bucketed ("19-35" instead of "27")
5. Compare with original - audit trail should explain every difference

**24.8 Test manual missing value fill**
1. If any missing values remain, POST to /jobs/{job_id}/fill-missing
2. Body: `{column: "student_name", row_indices: [5], values: ["John Doe"]}`
3. Export again, verify the value is filled

**24.9 Test outlier resolution**
1. GET /jobs/{job_id}/outliers
2. For one outlier, POST to /jobs/{job_id}/resolve-outlier
3. Body: `{row_index: 10, action: "remove"}`
4. Export again, verify that row is gone

**Next:** Check Phase 3 completion

---

### Step 25: Phase 3 Completion Checklist

**Go through this checklist:**
- [ ] CleanedDataset and CleaningLog tables exist in database
- [ ] Duplicates are detected and removed automatically
- [ ] Column names are normalized (lowercase, underscores, no spaces)
- [ ] Empty columns (>80% null) are removed
- [ ] Date columns are detected and converted to YYYY-MM format
- [ ] Age columns are detected and bucketed correctly
- [ ] Missing values in numeric columns are auto-filled with mean
- [ ] Outliers are detected using IQR method and flagged (not removed)
- [ ] Quality score is calculated (0-100)
- [ ] Cleaned DataFrame is cached in Redis
- [ ] Audit trail contains entry for every change
- [ ] Can view cleaning summary via API
- [ ] Can view full audit trail via API
- [ ] Can identify remaining missing fields
- [ ] Can manually fill missing values via API
- [ ] Can view flagged outliers
- [ ] Can resolve outliers (keep or remove)
- [ ] Can export cleaned CSV
- [ ] Exported CSV matches audit trail (every change is explained)

**If any checkbox fails:** Debug that specific feature before continuing.

**Next:** Move to Phase 4

---

## 🎯 PHASE 4: CHART GENERATION & AI RECOMMENDATIONS (Weeks 5-7)

### Overview
Now that data is clean, you'll generate visualizations and use AI to recommend which charts to create.

---

### Step 26: Create User Goal Model

**What:** Create a table to store the user's analytical goal ("Increase sales", "Improve performance", etc.)

**Why:** AI needs to know the user's goal to recommend relevant charts

**Do this:**
1. Create `app/models/user_goal.py`
2. Define model with fields:
   - `id`
   - `job_id` (foreign key, unique - one goal per upload)
   - `goal_text` (string - user's description)
   - `goal_category` (string - 'sales', 'performance', 'cost', 'custom')
   - `created_at`
3. Add relationship to UploadJob
4. Save file

**Next:** Create chart model

---

### Step 27: Create Chart Model

**What:** Create a table to store generated charts

**Why:** Need to save chart configuration and data for retrieval

**Do this:**
1. Create `app/models/chart.py`
2. Define model with fields:
   - `id`
   - `job_id` (foreign key)
   - `chart_type` (string - 'line', 'bar', 'scatter', 'pie', 'grouped_bar')
   - `x_header` (string - which column is X axis)
   - `y_header` (string - which column is Y axis)
   - `title` (string)
   - `config` (JSON - colors, labels, chart-specific options)
   - `data` (JSON - the actual chart data in Recharts format)
   - `is_recommended` (boolean - true if AI recommended this pairing)
   - `created_at`
3. Add relationship to UploadJob
4. Save file

**Next:** Create migrations

---

### Step 28: Create Migrations for Goal and Chart Models

**Do this:**
1. Terminal: `alembic revision --autogenerate -m "add user_goal and chart tables"`
2. Terminal: `alembic upgrade head`
3. Verify tables in database

**Next:** Build chart engine service

---

### Step 29: Build Chart Type Determination Logic

**What:** Create a service that decides which chart type to use based on data types

**Why:** You can't show a pie chart for two numeric columns - logic needs to match data

**Do this:**
1. Create `app/services/chart_engine.py`
2. Create class `ChartEngine`
3. In __init__, accept: job_id, DataFrame
4. Create method `determine_chart_type(x_col, y_col)`:
   - Check data type of x_col and y_col
   - Apply these rules:
     - If x is datetime/date column → LineChart
     - If x is categorical, y is numeric → BarChart
     - If both are numeric → ScatterChart
     - If single categorical (no y) → PieChart
     - If x is categorical, multiple y columns → GroupedBarChart
   - Return chart type as string
5. Save file

**Next:** Add chart data generation

---

### Step 30: Build Chart Data Generation

**What:** Convert Pandas DataFrame into JSON format that Recharts (React library) can use

**Why:** Charts need structured data: `[{x: value, y: value}, ...]`

**Do this:**
1. Open `app/services/chart_engine.py`
2. Add method `generate_chart_data(x_col, y_col, chart_type)`:
3. For LineChart / BarChart / ScatterChart:
   - Select x_col and y_col from DataFrame
   - Convert to list of dictionaries: `[{x: row[x_col], y: row[y_col]} for row in df.iterrows()]`
   - If categorical x, aggregate y values (sum or mean) by category
4. For PieChart:
   - Count frequency of each category
   - Return: `[{name: category, value: count}, ...]`
5. For all types:
   - Generate x-axis label (column name, formatted)
   - Generate y-axis label
   - Generate title (e.g., "Total Sales by Month")
6. Return dictionary: `{data: [...], xLabel: "...", yLabel: "...", title: "..."}`
7. Save file

**Next:** Add correlation heatmap

---

### Step 31: Build Correlation Heatmap Generator

**What:** Generate a correlation matrix for all numeric columns

**Why:** Shows relationships between variables (e.g., "sales and advertising spend are correlated")

**Do this:**
1. Open `app/services/chart_engine.py`
2. Add method `generate_correlation_heatmap()`:
   - Select only numeric columns from DataFrame
   - Calculate correlation matrix: `df.corr()`
   - Convert to JSON format: `{matrix: [[...]], columns: [...]}`
   - Return the JSON
3. Save file

**Next:** Build AI recommendation service

---

### Step 32: Build AI Header Recommendation Service

**What:** Use Claude API to recommend which column pairings are most relevant to user's goal

**Why:** Users shouldn't have to guess which charts to make - AI can suggest based on their goal

**Do this:**
1. Create `app/services/ai_recommendations.lpy`
2. Create class `AIRecommendationEngine`
3. In __init__, accept Anthropic API key
4. Create method `recommend_headers(column_names, data_sample, user_goal)`:
5. Build a prompt for Claude:
   - "You are analyzing a dataset with these columns: {column_names}"
   - "Here's a sample of the data: {data_sample}" (first 5 rows)
   - "The user's goal is: {user_goal}"
   - "Recommend 5 X vs Y column pairings that would be most relevant for this goal"
   - "Return ONLY valid JSON in this format: [{x_col, y_col, relevance_score, reasoning}, ...]"
6. Call Claude API:
   - Use `client.messages.create()` with model="claude-sonnet-4-20250514"
   - Parse the JSON response
   - Handle errors if response isn't valid JSON
7. Return list of recommendations
8. Save file

**Technical note:** You need to install Anthropic client: `pip install anthropic`

**Next:** Create chart API endpoints

---

### Step 33: Create Goal Setting Endpoint

**What:** Build API to let users set their analytical goal

**Do this:**
1. Create `app/routes/charts.py`
2. Create APIRouter with prefix="/jobs"
3. Build endpoint:

   **POST /jobs/{job_id}/goal**
   - Require authentication
   - Accept body: `{goal_text, goal_category}`
   - Verify job belongs to current user
   - Create or update UserGoal record
   - Return the goal

4. Save file
5. Register router in main.py

**Next:** Create recommendation endpoint

---

### Step 34: Create Chart Recommendation Endpoint

**What:** Build API that returns AI-recommended chart pairings

**Do this:**
1. Open `app/routes/charts.py`
2. Build endpoint:

   **GET /jobs/{job_id}/recommendations**
   - Require authentication
   - Get UserGoal for this job
   - Get cleaned DataFrame from Redis cache
   - Extract column names and first 5 rows as sample
   - Call AIRecommendationEngine.recommend_headers()
   - Return list of recommendations: `[{x_col, y_col, reasoning, score}]`

3. Save file

**Next:** Create chart generation endpoint

---

### Step 35: Create Chart Generation Endpoint

**What:** Build API to generate a chart from a column pairing

**Do this:**
1. Open `app/routes/charts.py`
2. Build endpoint:

   **POST /jobs/{job_id}/charts**
   - Require authentication
   - Accept body: `{x_col, y_col}`
   - Get cleaned DataFrame from Redis
   - Verify columns exist in DataFrame
   - Use ChartEngine to determine chart type
   - Use ChartEngine to generate chart data
   - Save Chart record to database
   - Return chart_id, type, data, config

3. Save file

**Next:** Create chart retrieval endpoints

---

### Step 36: Create Chart List and Detail Endpoints

**What:** Build APIs to list and retrieve saved charts

**Do this:**
1. Open `app/routes/charts.py`
2. Build endpoints:

   **GET /jobs/{job_id}/charts**
   - Return all charts for this job
   - Include: chart_id, type, title, x_col, y_col, is_recommended, created_at

   **GET /jobs/{job_id}/charts/{chart_id}**
   - Return specific chart with full data
   - Include: everything above + data, config

   **DELETE /jobs/{job_id}/charts/{chart_id}**
   - Delete chart record
   - Return success

3. Save file

**Next:** Create correlation endpoint

---

### Step 37: Create Correlation Heatmap Endpoint

**What:** Build API to get correlation matrix

**Do this:**
1. Open `app/routes/charts.py`
2. Build endpoint:

   **GET /jobs/{job_id}/correlation**
   - Get cleaned DataFrame from Redis
   - Use ChartEngine to generate correlation heatmap
   - Return: `{matrix: [[...]], columns: [...]}`

3. Save file

**Next:** Test chart generation

---

### Step 38: Test Chart Generation Flow

**Do this:**

**38.1 Set analytical goal**
1. POST to /jobs/{job_id}/goal
2. Body: `{goal_text: "Increase monthly sales", goal_category: "sales"}`
3. Verify goal is saved

**38.2 Get AI recommendations**
1. GET /jobs/{job_id}/recommendations
2. Should return 5 recommended pairings
3. Each should have: x_col, y_col, reasoning, relevance_score
4. Check that reasoning makes sense given your goal

**38.3 Generate a chart**
1. Pick one recommendation from step 38.2
2. POST to /jobs/{job_id}/charts
3. Body: `{x_col: "month", y_col: "total_sales"}`
4. Should return chart with:
   - chart_id
   - type (e.g., "line")
   - data array (Recharts-compatible format)
   - title

**38.4 List all charts**
1. GET /jobs/{job_id}/charts
2. Should show the chart you just created

**38.5 Get chart details**
1. GET /jobs/{job_id}/charts/{chart_id}
2. Should return full chart data

**38.6 Get correlation heatmap**
1. GET /jobs/{job_id}/correlation
2. Should return correlation matrix for all numeric columns

**38.7 Delete a chart**
1. DELETE /jobs/{job_id}/charts/{chart_id}
2. List charts again - deleted chart should be gone

**Next:** Check Phase 4 completion

---

### Step 39: Phase 4 Completion Checklist

**Go through this checklist:**
- [ ] Can set user goal via API
- [ ] AI recommendations return 5 relevant pairings
- [ ] Chart type is determined correctly based on column data types
- [ ] LineChart generated for time series data (date vs numeric)
- [ ] BarChart generated for category vs numeric
- [ ] ScatterChart generated for numeric vs numeric
- [ ] Chart data is in correct format for Recharts
- [ ] Can generate chart from any column pairing
- [ ] Can list all charts for a job
- [ ] Can retrieve specific chart by ID
- [ ] Can delete charts
- [ ] Correlation heatmap includes all numeric columns
- [ ] Correlation values are between -1 and 1
- [ ] Recommended charts are marked with is_recommended=true

**Next:** Move to Phase 5

---

## 🎯 PHASE 5: AI INSIGHTS & ANNOTATIONS (Weeks 7-8)

### Overview
Generate natural language explanations for charts using AI, with confidence scores.

---

### Step 40: Create Insight Model

**What:** Create a table to store AI-generated insights

**Do this:**
1. Create `app/models/insight.py`
2. Define model with fields:
   - `id`
   - `chart_id` (foreign key, nullable)
   - `job_id` (foreign key)
   - `content` (text - the AI-generated insight)
   - `confidence` (string - 'low', 'medium', 'high')
   - `confidence_score` (float 0.0-1.0)
   - `recommendations` (JSON - list of actionable suggestions)
   - `created_at`
3. Save file

**Next:** Create annotation model

---

### Step 41: Create Annotation Model

**What:** Create a table to store user annotations on charts

**Why:** Users should be able to add notes to specific data points (like "Spring promotion launched here")

**Do this:**
1. Create `app/models/annotation.py`
2. Define model with fields:
   - `id`
   - `chart_id` (foreign key)
   - `user_id` (foreign key)
   - `data_point_index` (integer - which point on the chart)
   - `text` (string - the annotation text)
   - `created_at`
3. Add relationships to Chart and User
4. Save file

**Next:** Create migrations

---

### Step 42: Create Migrations

**Do this:**
1. Terminal: `alembic revision --autogenerate -m "add insight and annotation tables"`
2. Terminal: `alembic upgrade head`
3. Verify tables exist

**Next:** Build insight generation service

---

### Step 43: Build AI Insight Generator

**What:** Create a service that generates natural language explanations for charts

**Do this:**
1. Create `app/services/ai_insights.py`
2. Create class `InsightGenerator`
3. In __init__, accept Anthropic API key
4. Create method `generate_insight(chart, user_goal, data_summary)`:
5. Build prompt for Claude:
   - "You are analyzing a {chart.chart_type} chart"
   - "X-axis: {chart.x_header}, Y-axis: {chart.y_header}"
   - "Data summary: mean={...}, median={...}, trend={...}, outliers={...}"
   - "User's goal: {user_goal}"
   - "Analyze this chart and provide:"
     - "1. What pattern or trend is shown?"
     - "2. How does this relate to the user's goal?"
     - "3. Actionable recommendations"
   - "Return ONLY valid JSON: {insight: string, confidence_score: float, recommendations: [{action, reasoning}]}"
6. Call Claude API
7. Parse response
8. Map confidence_score to category:
   - 0.0-0.4 → "low"
   - 0.4-0.7 → "medium"
   - 0.7-1.0 → "high"
9. Return parsed result
10. Save file

**Next:** Create insight endpoints

---

### Step 44: Create Insight Generation Endpoint

**What:** Build API to generate insights for charts

**Do this:**
1. Create `app/routes/insights.py`
2. Create APIRouter
3. Build endpoint:

   **POST /charts/{chart_id}/insights**
   - Require authentication
   - Get the Chart record
   - Get UserGoal for the job
   - Get cleaned DataFrame from Redis
   - Calculate data summary statistics for the chart columns
   - Call InsightGenerator.generate_insight()
   - Create Insight record in database
   - Return: insight_id, content, confidence, recommendations

4. Save file
5. Register router in main.py

**Next:** Create insight retrieval endpoints

---

### Step 45: Create Insight List and Detail Endpoints

**What:** Build APIs to retrieve insights

**Do this:**
1. Open `app/routes/insights.py`
2. Build endpoints:

   **GET /jobs/{job_id}/insights**
   - Return all insights for this job
   - Include: insight_id, chart_id, content, confidence, created_at

   **GET /insights/{insight_id}**
   - Return specific insight with full details
   - Include: everything + recommendations array

3. Save file

**Next:** Create annotation endpoints

---

### Step 46: Create Annotation Endpoints

**What:** Build APIs to add and manage chart annotations

**Do this:**
1. Create `app/routes/annotations.py`
2. Create APIRouter
3. Build endpoints:

   **POST /charts/{chart_id}/annotations**
   - Require authentication
   - Accept body: `{data_point_index, text}`
   - Verify chart exists
   - Create Annotation record
   - Return: annotation_id, text, user info, created_at

   **GET /charts/{chart_id}/annotations**
   - Return all annotations for this chart
   - Include user name with each annotation

   **DELETE /annotations/{annotation_id}**
   - Verify annotation belongs to current user
   - Delete annotation
   - Return success

4. Save file
5. Register router in main.py

**Next:** Test insights and annotations

---

### Step 47: Test AI Insights

**Do this:**

**47.1 Generate insight for a chart**
1. Make sure you have a chart created (from Phase 4)
2. POST to /charts/{chart_id}/insights
3. Wait for response (AI call takes 2-5 seconds)
4. Verify response contains:
   - Natural language insight
   - Confidence level (low/medium/high)
   - Specific recommendations

**47.2 Check insight quality**
1. Read the insight - does it make sense given the chart?
2. Check if it references the user's goal
3. Check if recommendations are actionable
4. If confidence is "low", the insight should use hedging language ("may", "suggests")

**47.3 List all insights**
1. GET /jobs/{job_id}/insights
2. Should show all insights generated

**47.4 Get specific insight**
1. GET /insights/{insight_id}
2. Should show full detail with recommendations array

**Next:** Test annotations

---

### Step 48: Test Chart Annotations

**Do this:**

**48.1 Add annotation to chart**
1. POST to /charts/{chart_id}/annotations
2. Body: `{data_point_index: 3, text: "Spring promotion launched"}`
3. Should return annotation_id

**48.2 List annotations**
1. GET /charts/{chart_id}/annotations
2. Should show the annotation with user info

**48.3 Add annotation from different user**
1. Login as different user
2. Try to access the same chart
3. Add another annotation
4. Both users' annotations should be visible

**48.4 Delete annotation**
1. DELETE /annotations/{annotation_id}
2. Verify it's removed
3. Try to delete another user's annotation - should fail

**Next:** Check Phase 5 completion

---

### Step 49: Phase 5 Completion Checklist

**Go through this checklist:**
- [ ] Can generate AI insight for any chart
- [ ] Insight references chart data correctly
- [ ] Insight relates to user's stated goal
- [ ] Confidence score is calculated (0.0-1.0)
- [ ] Confidence category is correct (low/medium/high)
- [ ] Recommendations are specific and actionable
- [ ] Can list all insights for a job
- [ ] Can retrieve specific insight by ID
- [ ] Can add annotation to specific data point on chart
- [ ] Can list all annotations for a chart
- [ ] Annotations show which user created them
- [ ] Can delete own annotations
- [ ] Cannot delete other users' annotations
- [ ] Multiple users can annotate the same chart

**Next:** Move to Phase 6

---

## 🎯 PHASE 6: MULTI-PERIOD COMPARISON (Weeks 8-9)

### Overview
Compare datasets from different time periods with fuzzy header matching.

---

### Step 50: Create Comparison Job Model

**What:** Create a table to track dataset comparisons

**Do this:**
1. Create `app/models/comparison_job.py`
2. Define model with fields:
   - `id`
   - `user_id` (foreign key)
   - `job_id_1` (foreign key to upload_jobs - Period 1)
   - `job_id_2` (foreign key to upload_jobs - Period 2)
   - `header_mapping` (JSON - maps file1 columns to file2 columns)
   - `status` (string - 'pending', 'completed', 'failed')
   - `created_at`
3. Save file
4. Create migration
5. Apply migration

**Next:** Build fuzzy matching service

---

### Step 51: Build Fuzzy Header Matching Service

**What:** Create a service that matches similar column names across two files

**Why:** "Sales Amount" and "Sale Total" are probably the same column - fuzzy matching finds these

**Do this:**
1. Create `app/services/comparison.py`
2. Install rapidfuzz: `pip install rapidfuzz`
3. Update requirements.txt
4. Create class `DatasetComparison`
5. In __init__, accept two DataFrames (df1, df2)
6. Create method `fuzzy_match_headers(threshold=85)`:
   - For each column in df1, compare to all columns in df2
   - Use `fuzz.ratio(col1, col2)` from rapidfuzz
   - If similarity > threshold (85%), mark as potential match
   - Return dictionary: `{df1_col: {df2_col, similarity_score}}`
7. Save file

**Next:** Add dataset alignment

---

### Step 52: Build Dataset Alignment

**What:** Create method to align two datasets based on header mapping

**Do this:**
1. Open `app/services/comparison.py`
2. Add method `align_datasets(mapping)`:
   - Accept mapping: `{df1_col: df2_col}`
   - Rename df2 columns to match df1 based on mapping
   - Keep only columns that exist in both datasets
   - Return: (aligned_df1, aligned_df2)
3. Save file

**Next:** Add delta calculation

---

### Step 53: Build Delta Calculator

**What:** Calculate percentage changes between two aligned datasets

**Do this:**
1. Open `app/services/comparison.py`
2. Add method `calculate_deltas(aligned_df1, aligned_df2)`:
   - For each numeric column:
     - Calculate: (df2_value - df1_value) / df1_value * 100
   - Handle division by zero (if df1_value is 0)
   - Return DataFrame with percentage changes
3. Add method `flag_significant_changes(deltas, threshold=20)`:
   - Flag any change > threshold %
   - Return list: `[{column, old_value, new_value, change_pct}]`
4. Save file

**Next:** Create comparison endpoints

---

### Step 54: Create Comparison API Endpoints

**What:** Build APIs for multi-period comparison

**Do this:**
1. Create `app/routes/comparison.py`
2. Create APIRouter with prefix="/compare"
3. Build endpoints:

   **POST /compare**
   - Accept body: `{job_id_1, job_id_2}`
   - Verify both jobs belong to current user
   - Get both cleaned DataFrames from Redis
   - Run fuzzy_match_headers()
   - Create ComparisonJob record with proposed header_mapping
   - Return: comparison_id, header_mapping (for user to review)

   **POST /compare/{comparison_id}/confirm-mapping**
   - Accept body: `{mapping: {col1: col2}}` (user can edit the mapping)
   - Update ComparisonJob with confirmed mapping
   - Run align_datasets()
   - Run calculate_deltas()
   - Run flag_significant_changes()
   - Update status to 'completed'
   - Return success

   **GET /compare/{comparison_id}/deltas**
   - Get the comparison deltas
   - Return: `[{column, period1_value, period2_value, change_pct}]`

   **GET /compare/{comparison_id}/significant-changes**
   - Get flagged significant changes
   - Return: `[{column, change_pct, likely_cause}]`

   **POST /compare/{comparison_id}/insights**
   - Generate AI insight explaining the comparison
   - Call Claude API with delta summary
   - Ask: "What are the top changes and why might they have occurred?"
   - Return insight

4. Save file
5. Register router in main.py

**Next:** Test comparison flow

---

### Step 55: Test Multi-Period Comparison

**Do this:**

**55.1 Prepare test files**
1. Create two CSV files with similar but not identical column names:
   - month1.csv: "Sales Amount", "Customer Count"
   - month2.csv: "Sale Total", "# of Customers"
2. Both should have same categories but different values

**55.2 Upload both files**
1. Upload month1.csv - get job_id_1
2. Upload month2.csv - get job_id_2
3. Wait for both to process

**55.3 Create comparison**
1. POST to /compare
2. Body: `{job_id_1: X, job_id_2: Y}`
3. Should return header_mapping showing:
   - "Sales Amount" → "Sale Total" (85% match)
   - "Customer Count" → "# of Customers" (80% match)

**55.4 Confirm mapping**
1. Review the proposed mapping
2. POST to /compare/{comparison_id}/confirm-mapping
3. Body: `{mapping: {confirmed pairs}}`
4. Should return success

**55.5 Get deltas**
1. GET /compare/{comparison_id}/deltas
2. Should show percentage change for each matched column

**55.6 Get significant changes**
1. GET /compare/{comparison_id}/significant-changes
2. Should flag any changes >20%

**55.7 Generate comparison insight**
1. POST to /compare/{comparison_id}/insights
2. AI should explain top changes and possible causes

**Next:** Check Phase 6 completion

---

### Step 56: Phase 6 Completion Checklist

**Go through this checklist:**
- [ ] Can create comparison between two upload jobs
- [ ] Fuzzy matching finds similar column names
- [ ] Similarity scores are accurate (85%+ for good matches)
- [ ] Can manually adjust header mappings
- [ ] Datasets align correctly based on mapping
- [ ] Percentage deltas calculated correctly
- [ ] Significant changes (>20%) are flagged
- [ ] Can retrieve delta list via API
- [ ] AI generates meaningful comparison insights
- [ ] Comparison insight explains top changes
- [ ] Can compare files with different numbers of columns

**All phases complete! Ready for frontend development.**

---

## 🎉 WHAT YOU'VE BUILT

After completing all 6 phases, you have:

### ✅ Complete Backend API
- 40+ API endpoints fully functional
- JWT-based authentication
- File upload to MinIO
- Background processing with Celery
- Full audit trail of all changes

### ✅ Data Processing Engine
- 4-phase cleaning pipeline
- Quality scoring (0-100)
- Duplicate detection
- Missing value handling
- Outlier detection
- Date standardization
- Age bucketing

### ✅ Visualization System
- AI-powered chart recommendations
- 5 chart types (line, bar, scatter, pie, grouped)
- Correlation heatmap
- Deterministic chart generation
- Recharts-compatible data format

### ✅ AI Integration
- Claude API for header recommendations
- Natural language insight generation
- Confidence scoring
- Actionable recommendations
- Multi-period comparison analysis

### ✅ Collaboration Features
- User annotations on charts
- Workspace support (database ready)
- Full audit trail export

---

## 📱 NEXT: FRONTEND DEVELOPMENT

Now you're ready to build the Next.js frontend that consumes all these APIs.

**Frontend will have these screens:**
1. Login/Register
2. Dashboard (list of uploads)
3. Upload page (drag-drop CSV)
4. Cleaning review (show quality score, audit trail, before/after)
5. Goal setting (text input for analytical goal)
6. Chart dashboard (show recommended + generated charts)
7. Insight view (show AI analysis with confidence badges)
8. Comparison view (upload two files, review mapping, see deltas)
9. Export page (download cleaned CSV)

But build the frontend AFTER all backend is working and tested!

---

## 🐛 General Debugging Tips

**API returns 500 error:**
- Check FastAPI terminal for full traceback
- Look for the actual error message (line number + error type)
- Most common: database field mismatch, Redis connection failed, MinIO timeout

**Celery task doesn't run:**
- Check Celery terminal - is worker running?
- Did you restart Celery after adding new task?
- Is Redis running? (`redis-cli ping`)

**Data doesn't look right:**
- Check audit trail - did cleaning steps actually run?
- Check Redis - is DataFrame cached?
- Try re-uploading and watch Celery logs

**AI returns weird responses:**
- Check the prompt you're sending
- Add explicit JSON formatting instructions
- Increase max_tokens if response is cut off
- Try different model (sonnet vs opus)

---

**You now have a complete, step-by-step plan from authentication to AI-powered analytics. Follow each step, test thoroughly, and build incrementally. Good luck! 🚀**