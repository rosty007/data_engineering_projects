import logging
import pathlib

import pandas as pd

logger = logging.getLogger(__name__)

log_dir = pathlib.Path(__file__).parent.parent / "logs"
data_dir = pathlib.Path(__file__).parent.parent / "data"
log_file = log_dir / "data_cleaning_pipeline.log"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def extract_data(filename: str) -> pd.DataFrame:
    """
    Extracts data from a CSV file.

    Parameters:
    filename (str): The name of the CSV file.

    Returns:
    pd.DataFrame: A DataFrame containing the extracted data.
    """
    try:
        file_path = data_dir / filename
        logger.info(f"Extracting data from {file_path}")
        data = pd.read_csv(file_path)
        logger.info(f"Data extraction completed successfully, extracted {len(data)} rows and {len(data.columns)} columns")
        return data
    except FileNotFoundError:
        logger.exception(f"File not found: {file_path}")
        raise
    except Exception:
        logger.exception(f"Error extracting data from CSV {file_path}")
        raise


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the extracted data.

    Parameters:
    data (pd.DataFrame): The DataFrame containing the extracted data.

    Returns:
    pd.DataFrame: A DataFrame containing the cleaned data.
    """
    try:
        logger.info("Cleaning data")
        # Example cleaning steps
        data = data.drop_duplicates()  # Drop duplicate rows
        data["customer_name"] = data["customer_name"].fillna("Unknown")  # Fill missing customer names
        data["amount"] = data["amount"].fillna(0)  # Fill missing order amounts with 0
        
        logger.info("Data cleaning completed successfully")
        return data
    except Exception:
        logger.exception("Error cleaning data")
        raise

def validate_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Validates the cleaned data.

    Parameters:
    data (pd.DataFrame): The DataFrame containing the cleaned data.

    Returns:
    pd.DataFrame: A DataFrame containing the validated data.
    """
    try:
        logger.info("Validating data")
        # Filter out orders with negative amounts
        data = data[data["amount"] >= 0]
        # Convert order_date to datetime, coerce errors to NaT
        data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")
        # Drop rows with missing order dates after conversion and handling mal formed dates
        data = data.dropna(subset=["order_date"])
        logger.info(f"Data validation completed successfully: {len(data)} rows remaining after validation")
        return data
    except Exception:
        logger.exception("Error validating data")
        raise

def save_data(data: pd.DataFrame, filename: str) -> None:
    """
    Saves the cleaned data to a CSV file.

    Parameters:
    data (pd.DataFrame): The DataFrame containing the cleaned data.
    filename (str): The name of the output CSV file.
    """
    try:
        output_path = data_dir / filename
        logger.info(f"Saving cleaned data to {output_path}")
        data.to_csv(output_path, index=False)
        logger.info(f"Data saving completed successfully to {output_path}")
    except Exception:
        logger.exception(f"Error saving cleaned data to {output_path}")
        raise

def run_pipeline(input_filename: str, output_filename: str) -> None:
    """
    Runs the data cleaning pipeline.

    Parameters:
    input_filename (str): The name of the input CSV file.
    output_filename (str): The name of the output CSV file.
    """
   
    logger.info("Starting data cleaning pipeline")
    data = extract_data(input_filename)
    cleaned_data = clean_data(data)
    validated_data = validate_data(cleaned_data)
    save_data(validated_data, output_filename)
    logger.info("Data cleaning pipeline completed successfully")

if __name__ == "__main__":
    input_file = "raw_data.csv"
    output_file = "cleaned_data.csv"
    run_pipeline(input_file, output_file)
    