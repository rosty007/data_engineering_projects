# CSV Data Cleaning Pipeline

## Overview

This project is a **data cleaning pipeline** written in Python. It reads a raw sales CSV file, removes duplicates, fills in missing values, filters out invalid records, standardizes dates, and writes the result to a new, clean CSV file. The original file is never modified.

The pipeline is organized in four small steps (extract, clean, validate, save) and every step is logged to a file, so each run can be audited afterwards.

## Problem Statement

Raw data exports are rarely ready for analysis. A typical sales file contains problems such as:

- **duplicated rows** that inflate totals,
- **missing customer names and amounts** that break grouping and aggregations,
- **negative amounts** that do not represent valid orders,
- **dates stored as text**, sometimes malformed, that cannot be sorted or filtered by period.

Cleaning these issues by hand in a spreadsheet is slow, error-prone and impossible to reproduce. This pipeline applies the same documented rules every time, so the output is consistent and the process can be repeated on any new export.

## Tech Stack

| Component | Purpose |
|---|---|
| **Python 3.9+** | Core language |
| **pandas** | Reading, cleaning, validating and writing the data |
| **logging** (standard library) | Execution log written to `logs/data_cleaning_pipeline.log` |
| **pathlib** (standard library) | Portable file paths |

## Project Structure

```
project_3_data_cleaning/
├── README.md
├── requirements.txt
├── data/
│   ├── raw_data.csv                  # Input: raw data (you provide it)
│   └── cleaned_data.csv              # Output: cleaned data (generated)
├── logs/
│   └── data_cleaning_pipeline.log    # Execution log (generated)
└── scripts/
    └── cleaning_pipeline.py          # The cleaning pipeline
```

## Pipeline Flow

```
raw_data.csv  ──►  Extract  ──►  Clean  ──►  Validate  ──►  Save  ──►  cleaned_data.csv
```

### 1. Extract
`extract_data()` reads the CSV file from the `data/` folder into a pandas DataFrame and logs the number of rows and columns. If the file is missing or unreadable, the error is logged with its traceback and the pipeline stops.

### 2. Clean
`clean_data()` fixes the structural problems of the data:

1. **Remove duplicates:** fully identical rows are dropped.
2. **Fill missing customer names:** empty values in `customer_name` become `"Unknown"`.
3. **Fill missing amounts:** empty values in `amount` become `0`.

### 3. Validate
`validate_data()` removes the records that are not usable:

1. **Remove negative amounts:** only rows with `amount >= 0` are kept.
2. **Parse dates:** `order_date` is converted to a real datetime type. Values that cannot be parsed become `NaT` (null) instead of stopping the pipeline.
3. **Remove rows without a valid date:** rows where `order_date` is `NaT` after conversion are dropped.

### 4. Save
`save_data()` writes the validated DataFrame to the output CSV file in the `data/` folder, without the pandas index.

### Orchestration and logging
`run_pipeline()` runs the four steps in order. Each stage writes timestamped messages to `logs/data_cleaning_pipeline.log`, including a full traceback if an error occurs.

## How to Run

### Prerequisites

- Python 3.9 or later
- An input CSV file named `raw_data.csv` in the `data/` folder, containing at least the columns `customer_name`, `amount` and `order_date`

### 1. Get the project

```bash
cd project_3_data_cleaning
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

### 4. Place the input file

Put your raw file at `data/raw_data.csv`. The `data/` and `logs/` folders are created automatically by the script if they do not exist.

### 5. Run the pipeline

From the project root:

```bash
python scripts/cleaning_pipeline.py
```

To use other file names, edit the `input_file` and `output_file` variables at the bottom of `scripts/cleaning_pipeline.py`.

### 6. Check the results

- **Cleaned file:** open `data/cleaned_data.csv`
- **Log file:** `cat logs/data_cleaning_pipeline.log`

### 7. Deactivate the virtual environment (when finished)

```bash
deactivate
```

## Sample Output

> The example below uses a small sample file. Log timestamps and file paths are illustrative and will differ on your machine.

**Input (`data/raw_data.csv`):**

```text
order_id,customer_name,product,amount,order_date
1,Alice,Laptop,1200,2025-01-10
2,Bob,Phone,-800,2025-01-11
3,Charlie,Tablet,,2025-01-32
3,Charlie,Tablet,,2025-01-32
4,,Monitor,300,2025-01-13
```

**Output (`data/cleaned_data.csv`):**

```text
order_id,customer_name,product,amount,order_date
1,Alice,Laptop,1200.0,2025-01-10
4,Unknown,Monitor,300.0,2025-01-13
```

What happened to each input row:

| Order | Result | Reason |
|---|---|---|
| 1 (Alice) | Kept | Valid row |
| 2 (Bob) | Removed | Negative amount (`-800`) |
| 3 (Charlie), twice | Removed | The duplicate was dropped, the missing amount was set to `0`, then the row was removed because `2025-01-32` is not a valid date |
| 4 (no name) | Kept | The missing customer name became `Unknown` |

Amounts are written as `1200.0` and `300.0` because the column contained a missing value, which makes pandas store it as a decimal number.

**Log file (`logs/data_cleaning_pipeline.log`):**

```text
2026-10-11 01:10:03,201 - INFO - Starting data cleaning pipeline
2026-10-11 01:10:03,202 - INFO - Extracting data from /.../project_3_data_cleaning/data/raw_data.csv
2026-10-11 01:10:03,215 - INFO - Data extraction completed successfully, extracted 5 rows and 5 columns
2026-10-11 01:10:03,215 - INFO - Cleaning data
2026-10-11 01:10:03,221 - INFO - Data cleaning completed successfully
2026-10-11 01:10:03,221 - INFO - Validating data
2026-10-11 01:10:03,230 - INFO - Data validation completed successfully: 2 rows remaining after validation
2026-10-11 01:10:03,230 - INFO - Saving cleaned data to /.../project_3_data_cleaning/data/cleaned_data.csv
2026-10-11 01:10:03,236 - INFO - Data saving completed successfully to /.../project_3_data_cleaning/data/cleaned_data.csv
2026-10-11 01:10:03,236 - INFO - Data cleaning pipeline completed successfully
```

## Notes and Limitations

- **Rows are removed silently.** Records with negative amounts or invalid dates are dropped, and the log only reports how many rows remain. Logging the number of removed rows per rule, or saving them to a separate "rejected" file, would make the process more transparent.
- **Required columns.** The pipeline expects `customer_name`, `amount` and `order_date`; a missing column raises an error that is written to the log. Other columns are kept unchanged.
- **Numeric amounts.** The `amount` column must be numeric. Text values in that column make the comparison with `0` fail.
- **Business rules.** Replacing missing amounts with `0` is a simplification: depending on the use case, a missing amount may be better kept as null or investigated.
- **File names.** The input and output file names are set in the script rather than passed on the command line.

## Key Learnings

This project demonstrates the following skills and concepts:

- **Data cleaning with pandas:** deduplication, handling missing values, boolean filtering and type conversion with graceful error handling (`errors='coerce'`).
- **Data validation:** separating structural cleaning from business-rule validation.
- **Pipeline design:** splitting the work into small, single-purpose, testable functions chained by an orchestrator.
- **Error handling and logging:** catching exceptions, logging tracebacks with `logger.exception`, and re-raising so failures are never silent.
- **Reproducibility:** documented rules, a virtual environment and a `requirements.txt` so anyone can rerun the process and get the same result.
- **Path handling:** using `pathlib` so the script works regardless of the directory it is launched from.

## Possible Improvements

- Log the number of rows removed by each rule and save rejected rows to a separate file.
- Accept input and output file names as command-line arguments (`argparse`).
- Validate the schema (required columns and types) before cleaning.
- Add unit tests for `clean_data()` and `validate_data()` with `pytest`.
- Load the cleaned data into a database as a next step.