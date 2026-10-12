# JSON to PostgreSQL ETL Pipeline

## Overview

This project is an **ETL (Extract, Transform, Load) pipeline** written in Python that handles **nested JSON data**. It reads a JSON file of orders, where each order contains a list of purchased items, and splits it into two relational tables: one with one row per order and one with one row per item. Both tables are then loaded into a **PostgreSQL** database and linked by `order_id`.

Every step is logged to a file, and database credentials are kept outside the code in a `.env` file.

## Problem Statement

Orders often come from web applications and APIs as JSON, where one order contains a list of items nested inside it. This structure is natural for applications but hard to use for analysis:

- SQL queries and BI tools expect flat tables, not nested lists.
- Storing the items inside the order row would duplicate order data or hide the items in a single column.
- Questions such as "which products sell the most?" or "what is the revenue per order?" require one row per item.

This pipeline solves that by flattening the JSON and splitting it into a normalized two-table model (orders and items). Analysts can then query and join the data with standard SQL.

## Tech Stack

| Component | Purpose |
|---|---|
| **Python 3.9+** | Core language |
| **pandas** | Flattening the JSON (`json_normalize`, `explode`) and building the tables |
| **SQLAlchemy** | Database connection and loading (`DataFrame.to_sql`) |
| **psycopg2** | PostgreSQL driver used by SQLAlchemy |
| **python-dotenv** | Loading database credentials from a `.env` file |
| **PostgreSQL** | Target relational database |
| **json** and **logging** (standard library) | Reading the file and writing the execution log to `logs/json_pipeline.log` |

## Project Structure

```
project_4_json_pipeline/
├── README.md
├── requirements.txt
├── config/
│   └── .env                  # Database credentials (not committed to Git)
├── data/
│   └── orders.json           # Input: nested orders (you provide it)
├── logs/
│   └── json_pipeline.log     # Execution log (created automatically)
└── scripts/
    └── json_pipeline.py      # The ETL pipeline
```

## Pipeline Flow

```
orders.json  ──►  Extract  ──►  Transform  ──►  Load  ──►  PostgreSQL (tables: orders, orders_items)
```

### 1. Extract
`extract_json_data()` opens the JSON file from the `data/` folder, parses it, and converts it to a pandas DataFrame with `pd.json_normalize`. Nested dictionaries (other than lists) are flattened into columns whose names use dots, such as `customer.city`.

### 2. Transform
`transform_data()` turns the single nested DataFrame into two related tables:

1. **Explode the items:** the `items` column holds a list per order; `explode` creates one row per item.
2. **Build `df_orders`:** all columns except `items`, with duplicates removed, so that there is exactly one row per order.
3. **Build `df_items`:** each item dictionary is expanded into columns, and the parent `order_id` is added to every item row so that the two tables can be joined.

### 3. Load
`load_data()` creates a SQLAlchemy engine and writes the two DataFrames to PostgreSQL with `if_exists='replace'`:

| Table | Content |
|---|---|
| `orders` | One row per order |
| `orders_items` | One row per purchased item, linked to its order through `order_id` |

On every run, both tables are **dropped and recreated** from the JSON file, so the database always mirrors the latest input.

### Orchestration and logging
`run_pipeline()` runs the three steps in order. Each stage writes timestamped messages to `logs/json_pipeline.log`, including a full traceback if an error occurs.

## Database Schema

Both tables are created by the pipeline, so there is nothing to set up manually. Column names and types are inferred by pandas from the JSON content.

```
orders (1) ──────────< (many) orders_items
  order_id                      order_id   (links each item to its order)
  ...other order fields         ...item fields (for example product, quantity, price)
```

> **Important:** because the load uses `if_exists='replace'`, any table with the same name that already exists is dropped and replaced. The recreated tables have no primary key, foreign key or index. If you need them, create the tables yourself, switch the load to `if_exists='append'` and empty the tables before each run.

## How to Run

### Prerequisites

- Python 3.9 or later
- A running PostgreSQL server and an existing database
- A PostgreSQL user with permission to create and drop tables in that database
- An input file named `orders.json` in the `data/` folder (see the format below)

### Expected input format

The file must contain a list of orders. Each order must have an `order_id` and an `items` list:

```json
[
  {
    "order_id": 1,
    "customer_name": "Alice",
    "order_date": "2025-01-10",
    "items": [
      {"product": "Laptop", "quantity": 1, "price": 1200.0},
      {"product": "Mouse", "quantity": 2, "price": 25.0}
    ]
  }
]
```

Other order-level fields can be added freely; they are kept in the `orders` table.

### 1. Get the project

```bash
cd project_4_json_pipeline
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

Create the file `config/.env` with the following content, adapted to your setup (the `config/` folder is created by the script if it does not exist):

```env
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
```

| Variable | Description |
|---|---|
| `DB_USER` / `DB_PASSWORD` | PostgreSQL credentials (special characters are URL-encoded automatically) |
| `DB_HOST` / `DB_PORT` | Database server address and port |
| `DB_NAME` | Name of the target database |

> **Security:** never commit `config/.env` to version control. Add it to your `.gitignore`.

### 5. Place your input data

Put your JSON file at `data/orders.json`. To use another file name, edit the `json_file_name` variable at the bottom of `scripts/json_pipeline.py`.

### 6. Run the pipeline

From the project root:

```bash
python scripts/json_pipeline.py
```

### 7. Check the results

- **Log file:** `cat logs/json_pipeline.log`
- **Database:**

```sql
SELECT * FROM orders;
SELECT * FROM orders_items;
SELECT COUNT(*) FROM orders o JOIN orders_items i USING (order_id);
```

### 8. Deactivate the virtual environment (when finished)

```bash
deactivate
```

## Sample Output

> The example below uses a small illustrative file. Log timestamps and file paths will differ on your machine, and your columns will match your own JSON.

**Input (`data/orders.json`):**

```json
[
  {
    "order_id": 1,
    "customer_name": "Alice",
    "order_date": "2025-01-10",
    "items": [
      {"product": "Laptop", "quantity": 1, "price": 1200.0},
      {"product": "Mouse", "quantity": 2, "price": 25.0}
    ]
  },
  {
    "order_id": 2,
    "customer_name": "Bob",
    "order_date": "2025-01-11",
    "items": [
      {"product": "Monitor", "quantity": 1, "price": 300.0}
    ]
  }
]
```

**Table `orders`** (one row per order):

```text
 order_id | customer_name | order_date
----------+---------------+------------
        1 | Alice         | 2025-01-10
        2 | Bob           | 2025-01-11
```

**Table `orders_items`** (one row per item):

```text
 product | quantity | price | order_id
---------+----------+-------+----------
 Laptop  |        1 |  1200 |        1
 Mouse   |        2 |    25 |        1
 Monitor |        1 |   300 |        2
```

**Log file (`logs/json_pipeline.log`):**

```text
2026-10-12 18:30:02,114 - INFO - Successfully extracted data from /.../project_4_json_pipeline/data/orders.json: 2 rows
2026-10-12 18:30:02,131 - INFO - Successfully transformed the data into df_orders (2 rows) and df_items DataFrames (3 rows)
2026-10-12 18:30:02,402 - INFO - Successfully loaded data into the database: 2 rows into 'orders' and 3 rows into 'orders_items'
2026-10-12 18:30:02,402 - INFO - ETL pipeline completed successfully
```

## Notes and Limitations

- **Full refresh on every run.** The load replaces both tables, so running the pipeline twice on the same file is safe and gives the same result. The flip side is that **all previous data is deleted** on each run, so this approach is not suitable for incremental loads or for keeping history.
- **The two tables are not loaded atomically.** `orders` and `orders_items` are written one after the other. If the second write fails, `orders` has already been replaced while `orders_items` still holds the previous data, leaving the two tables out of sync. Loading both inside a single transaction would prevent this.
- **No constraints or indexes.** The recreated tables have no primary key, foreign key, index or `NOT NULL` constraint, so the link between orders and items is a convention rather than something enforced by the database.
- **Inferred types.** Column types come from pandas. Dates such as `order_date` stay as text unless they are converted in the transform step.
- **Required fields.** Each order needs an `order_id` and an `items` field. A missing field raises an error that is written to the log.
- **Orders without items.** An order whose `items` list is empty produces a row with no item data, which can add an empty column to `orders_items`. Filtering such orders out (or handling them explicitly) is advisable if your data can contain them.
- **Environment variables.** The database variables are read without validation. If `config/.env` is missing or incomplete, the script stops with an error in the console that is not written to the log file.
- **File name.** The input file name is set in the script rather than passed on the command line.

## Key Learnings

This project demonstrates the following skills and concepts:

- **Handling nested JSON:** flattening semi-structured data with `pd.json_normalize` and expanding lists of records with `explode`.
- **Data modeling:** turning a one-to-many structure (an order and its items) into two related tables joined by a shared key.
- **ETL design:** separating extraction, transformation and loading into small, testable functions.
- **Database integration:** loading several DataFrames into PostgreSQL with SQLAlchemy and understanding the effect of `if_exists='replace'` on table schemas.
- **Error handling and logging:** logging tracebacks with `logger.exception` and re-raising so that failures are never silent.
- **Configuration management:** keeping credentials out of the code with environment variables and `python-dotenv`, and URL-encoding credentials safely.
- **Project hygiene:** a clear folder structure, a virtual environment, a `requirements.txt` for reproducibility, and documented code with type hints.

## Possible Improvements

- Load both tables in a single transaction so that they always stay consistent.
- Define the schema explicitly (primary key on `orders.order_id`, foreign key on `orders_items.order_id`, proper date types).
- Handle orders with empty `items` lists explicitly.
- Convert date columns to real dates in the transform step.
- Validate the JSON structure (required fields and types) before transforming.
- Accept the input file name as a command-line argument (`argparse`).
- Add unit tests for `transform_data()` with `pytest`.