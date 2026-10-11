import json
import logging
import os
import pathlib
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

log_dir = pathlib.Path(__file__).parent.parent / "logs"
data_dir = pathlib.Path(__file__).parent.parent / "data"
config_dir = pathlib.Path(__file__).parent.parent / "config"
log_file = log_dir / "json_pipeline.log"
log_dir.mkdir(exist_ok=True)
data_dir.mkdir(exist_ok=True)
config_dir.mkdir(exist_ok=True)

load_dotenv(config_dir / ".env")

logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def extract_json_data(json_file_name) -> pd.DataFrame:
    """
    Extracts data from a JSON file and returns it as a pandas DataFrame.

    Parameters:
    json_file_name (str): The name of the JSON file.

    Returns:
    pd.DataFrame: A DataFrame containing the extracted data.
    """
    json_file_path = data_dir / json_file_name
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        df = pd.json_normalize(data)
        logger.info(f"Successfully extracted data from {json_file_path}: {len(df)} rows")
        return df
    except Exception:
        logger.exception(f"Error extracting data from {json_file_path}")
        raise


def transform_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transforms the DataFrame by performing necessary data cleaning and transformations.

    Parameters:
    df (pd.DataFrame): The DataFrame to be transformed.

    Returns:
    tuple[pd.DataFrame, pd.DataFrame]: A tuple containing the transformed order DataFrame and item DataFrame.
    """
    try:
        columns = list(df.columns)
        columns.remove('items')
        df = df.explode('items', ignore_index=True)
        df_orders = df[columns].drop_duplicates()
        df_items = df['items'].apply(pd.Series)
        df_items['order_id'] = df['order_id']
        

        logger.info(f"Successfully transformed the data into df_orders ({len(df_orders)} rows)"
                    f" and df_items DataFrames ({len(df_items)} rows)")
        return df_orders, df_items
    except Exception:
        logger.exception("Error transforming the data")
        raise


def load_data(df_orders: pd.DataFrame, df_items: pd.DataFrame, connection_string: str) -> None:
    """
    Loads the transformed DataFrames into a database.

    Parameters:
    df_orders (pd.DataFrame): The transformed order DataFrame.
    df_items (pd.DataFrame): The transformed item DataFrame.
    connection_string (str): The database connection string.

    Returns:
    None
    """
    try:
        from sqlalchemy import create_engine

        engine = create_engine(connection_string)
        df_orders.to_sql('orders', con=engine, if_exists='replace', index=False)
        df_items.to_sql('orders_items', con=engine, if_exists='replace', index=False)

        logger.info(f"Successfully loaded data into the database: {len(df_orders)} "
                    f" rows into 'orders' and {len(df_items)} rows into 'orders_items'")
    except Exception:
        logger.exception("Error loading data into the database")
        raise

def run_pipeline(json_file_name: str, connection_string: str) -> None:
    """
    Runs the entire ETL pipeline: extract, transform, and load.

    Parameters:
    json_file_name (str): The name of the JSON file to extract data from.
    connection_string (str): The database connection string.

    Returns:
    None
    """
   
    df = extract_json_data(json_file_name)
    df_orders, df_items = transform_data(df)
    load_data(df_orders, df_items, connection_string)
    logger.info("ETL pipeline completed successfully")
    

if __name__ == "__main__":
    # Example usage
    json_file_name = "orders.json"  # Replace with your JSON file name

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = quote_plus(db_user)
    db_password = quote_plus(db_password)
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    run_pipeline(json_file_name, connection_string)
    