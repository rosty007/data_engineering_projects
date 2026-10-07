# CSV to PostgreSQL ETL Pipeline

## Overview

This project is a simple, end-to-end **ETL (Extract, Transform, Load) pipeline** written in Python. It reads raw sales data from a CSV file, cleans it with `pandas`, and loads it into a `sales` table in a **PostgreSQL** database. Every step is logged to a file so each run can be audited afterwards.

Configuration (file name, database credentials) is kept outside the code in a `.env` file, so no secret is ever hard-coded.

## Problem Statement

Sales data often arrives as flat CSV exports. In that form it is hard to query, to share across teams, or to combine with other data sources. Raw exports also tend to be messy:

- duplicated rows that inflate revenue figures,
- missing amounts that break aggregations,
- dates stored as plain text that cannot be sorted or filtered by period.

This pipeline solves that by automating the path from raw CSV to a clean, queryable SQL table. Analysts and BI tools can then work from one reliable source, and the process is repeatable instead of being a manual copy-paste job.

## Tech Stack

| Component | Purpose |
|---|---|
| **Python 3.9+** | Core language |
| **pandas** | Reading the CSV and transforming the data |
| **SQLAlchemy** | Database connection and loading (`DataFrame.to_sql`) |
| **psycopg2** | PostgreSQL driver used by SQLAlchemy |
| **python-dotenv** | Loading configuration from a `.env` file |
| **PostgreSQL** | Target relational database |
| **logging** (standard library) | Execution log written to `log/pipeline.log` |

## Project Structure

```
project_1_csv_pipeline/
├── README.md
├── requirements.txt
├── config/
│   └── .env              # Environment variables (not committed to Git)
├── data/
│   └── sales_data.csv    # Input data
├── log/
│   └── pipeline.log      # Execution log (created automatically)
└── scripts/
    ├── __init__.py
    └── etl_pipeline.py   # The ETL pipeline
```

## Pipeline Flow

```
CSV file  ──►  Extract  ──►  Transform  ──►  Load  ──►  PostgreSQL (table: sales)
```

### 1. Extract
`extract_data()` reads the CSV file from the `data/` folder into a pandas DataFrame and logs the number of rows read.

### 2. Transform
`transform_data()` applies three cleaning rules:

1. **Remove duplicates**: fully identical rows are dropped.
2. **Fill missing amounts**: empty values in the `amount` column are replaced by `0`.
3. **Parse dates**: the `order_date` column is converted to a real datetime type. Values that cannot be parsed become `NaT` (null) instead of stopping the pipeline.

### 3. Load
`load_data()` creates a SQLAlchemy engine from the connection string and **appends** the DataFrame to the existing `sales` table. The table must be created beforehand (see [Database Schema](#database-schema)), and its constraints (such as the primary key on `order_id`) are enforced by PostgreSQL during the load.

### Orchestration and logging
`run_pipeline()` runs the three steps in order. Every stage writes timestamped messages to `log/pipeline.log`.

## Database Schema

The target table is created manually in PostgreSQL before running the pipeline:

```sql
CREATE TABLE sales (
    order_id      INT PRIMARY KEY,
    customer_name TEXT,
    product       TEXT,
    quantity      INT,
    amount        FLOAT,
    order_date    DATE
);
```

| Column | Type | Description |
|---|---|---|
| `order_id` | INT (primary key) | Unique identifier of the order |
| `customer_name` | TEXT | Name of the customer |
| `product` | TEXT | Product purchased |
| `quantity` | INT | Number of units ordered |
| `amount` | FLOAT | Order amount (missing values are set to `0` by the pipeline) |
| `order_date` | DATE | Date of the order |

The CSV file must have columns with these same names, since `to_sql` maps DataFrame columns to table columns by name.

## How to Run

### Prerequisites

- Python 3.9 or later
- A running PostgreSQL server and an existing database
- The `sales` table, created beforehand (see [Database Schema](#database-schema))
- A PostgreSQL user with permission to insert rows into that table

### 1. Get the project

```bash
cd project_1_csv_pipeline
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
```

Activate it:

```bash
# Linux / macOS
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

Your terminal prompt should now start with `(venv)`.

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the environment variables

Create the file `config/.env` with the following content, adapted to your setup:

```env
CSV_FILE_PATH=sales_data.csv

DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
```

| Variable | Description |
|---|---|
| `CSV_FILE_PATH` | Name of the CSV file located in the `data/` folder |
| `DB_USER` / `DB_PASSWORD` | PostgreSQL credentials (special characters are URL-encoded automatically) |
| `DB_HOST` / `DB_PORT` | Database server address and port |
| `DB_NAME` | Name of the target database |

> **Security:** never commit `config/.env` to version control. Add it to your `.gitignore`.

### 5. Create the table and place your input data

Run the `CREATE TABLE` statement from the [Database Schema](#database-schema) section in your database (with `psql` or any SQL client). Then make sure your CSV file is in the `data/` folder, with the columns `order_id`, `customer_name`, `product`, `quantity`, `amount` and `order_date`.

### 6. Run the pipeline

From the project root:

```bash
python scripts/etl_pipeline.py
```

### 7. Check the results

- **Log file:** `cat log/pipeline.log`
- **Database:**

```sql
SELECT COUNT(*) FROM sales;
SELECT * FROM sales LIMIT 5;
```

### 8. Deactivate the virtual environment (when finished)

```bash
deactivate
```

## Sample Output

> The values below are illustrative; your numbers will depend on your CSV file.

**Log file (`log/pipeline.log`):**

```text
2026-10-09 02:30:12,401 - INFO - Starting ETL pipeline
2026-10-09 02:30:12,402 - INFO - Extracting data from /.../project_1_csv_pipeline/data/sales_data.csv
2026-10-09 02:30:12,418 - INFO - Extracted 1000 rows successfully from /.../project_1_csv_pipeline/data/sales_data.csv
2026-10-09 02:30:12,418 - INFO - Transforming data
2026-10-09 02:30:12,431 - INFO - Data transformed successfully
2026-10-09 02:30:12,431 - INFO - Loading data into the database
2026-10-09 02:30:12,689 - INFO - Loaded 987 rows into the database successfully
2026-10-09 02:30:12,689 - INFO - ETL pipeline completed successfully
```

In this example, 13 duplicate rows were removed during the transform step (1000 extracted, 987 loaded).

**Database check:**

```sql
SELECT COUNT(*) FROM sales;
```

```text
 count
-------
   987
```

```sql
SELECT * FROM sales LIMIT 3;
```

```text
 order_id | customer_name |   product   | quantity | amount | order_date
----------+---------------+-------------+----------+--------+------------
        1 | Alice Martin  | Laptop      |        1 |   899.0 | 2026-01-05
        2 | Bob Dupont    | Mouse       |        2 |    35.5 | 2026-01-06
        3 | Chloe Bernard | Keyboard    |        1 |       0 | 2026-01-07
```

## Notes and Limitations

- **Re-running fails on the same data.** The load step appends rows, and `order_id` is a primary key. Running the pipeline a second time on the same file raises a unique-constraint violation instead of creating duplicates. To reload, run `TRUNCATE TABLE sales;` first, or add an upsert (`INSERT ... ON CONFLICT`) step to make the pipeline idempotent.
- **Duplicate `order_id` values in the CSV.** `drop_duplicates()` only removes rows that are identical in every column. Two different rows sharing the same `order_id` will make the load fail on the primary key.
- **Minimal validation.** The pipeline assumes the CSV columns match the table, and the transform step expects `amount` and `order_date`. A missing column or a type mismatch raises an error visible in the console.
- **Missing dates.** Unparseable dates become null (`NaT`) and are loaded as `NULL`, which the schema allows because `order_date` is not declared `NOT NULL`.

## Key Learnings

This project demonstrates the following skills and concepts:

- **ETL design:** separating extraction, transformation and loading into small, testable functions.
- **Data cleaning with pandas:** deduplication, handling missing values, type conversion with graceful error handling (`errors='coerce'`).
- **Database integration:** connecting Python to PostgreSQL with SQLAlchemy and loading data with `to_sql`.
- **Data modeling:** defining a relational schema with explicit column types and a primary key to guarantee data integrity.
- **Configuration management:** keeping credentials out of the code with environment variables and `python-dotenv`, and URL-encoding credentials safely.
- **Logging:** building an audit trail with Python's `logging` module.
- **Project hygiene:** a clear folder structure, a Python virtual environment, a `requirements.txt` for reproducibility, and documented code (docstrings and type hints).
- **Path handling:** using `pathlib` so the script works regardless of the directory it is launched from.

## Possible Improvements

- Add data-quality checks (schema validation, row-count checks).
- Make loads idempotent (upsert with `ON CONFLICT`, or truncate-and-load).
- Add error handling and retries around the database connection.
- Add unit tests for `transform_data()` with `pytest`.
- Schedule the pipeline (cron or Airflow) and containerize it with Docker.