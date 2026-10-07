import logging
import os
import pathlib
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Set up directories and logging from this script's location
conf_dir = pathlib.Path(__file__).parent.parent / "config"
log_dir = pathlib.Path(__file__).parent.parent / "log"
log_file = log_dir / "pipeline.log"
data_dir = pathlib.Path(__file__).parent.parent / "data"

# Create directories if they don't exist
os.makedirs(log_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

# Load environment variables from the .env file
load_dotenv(conf_dir / ".env")

# Set up logging
logger = logging.getLogger(__name__)
# Configure logging to write to a file with INFO level and a specific format
logging.basicConfig(filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')


def extract_data(file_path: str) -> pd.DataFrame:
    """
    Extract data from a CSV file.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Extracted data.
    """
    logger.info(f"Extracting data from {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Extracted {len(df)} rows successfully from {file_path}")
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform the data.

    Args:
        df (pd.DataFrame): Data to be transformed.

    Returns:
        pd.DataFrame: Transformed data.
    """
    logger.info("Transforming data")
    # Drop duplicates, fill missing values, and convert date columns
    df = df.drop_duplicates()
    df['amount'] = df['amount'].fillna(0)
    df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
    
    logger.info("Data transformed successfully")
    return df


def load_data(df: pd.DataFrame, connection_string: str) -> None:
    """
    Load data into the database.

    Args:
        df (pd.DataFrame): Data to be loaded.
        connection_string (str): Database connection string.
    Returns:
        None
    Raises:
        Exception: If there is an error while loading data into the database.
    """
    logger.info("Loading data into the database")
    # Create a database connection using SQLAlchemy based on the provided connection string
    db_connection = create_engine(connection_string)
    # Load the DataFrame into the 'sales' table in the database, replacing if it already exists
    df.to_sql('sales', db_connection, if_exists='replace', index=False)
    logger.info(f"Loaded {len(df)} rows into the database successfully")


def run_pipeline(file_path: str, connection_string: str) -> None:
    """
    Run the ETL pipeline.

    Args:
        file_path (str): Path to the CSV file.
        connection_string (str): Database connection string.

    Returns:
        None
    """

    logger.info("Starting ETL pipeline")
    # Execute Extract, transform, and load data tasks in sequence
    df = extract_data(file_path)
    df = transform_data(df)
    load_data(df, connection_string)
    logger.info("ETL pipeline completed successfully")


if __name__ == "__main__":
    # Get the CSV file name from environment variables and construct the full path
    file_name = os.getenv("CSV_FILE_PATH")
    file_path = data_dir / file_name

    # Get database connection parameters from environment variables
    db_user = os.getenv("DB_USER")
    # URL encode the username and password to handle special characters
    db_user = quote_plus(db_user)  # URL encode the username
    db_password = os.getenv("DB_PASSWORD")
    db_password = quote_plus(db_password)  # URL encode the password
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    # Construct the postgresql database connection string using the parameters
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    # Run the ETL pipeline with the specified file path and connection string
    run_pipeline(file_path, connection_string)