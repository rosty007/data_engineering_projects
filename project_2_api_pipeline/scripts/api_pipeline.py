import logging
import os
import pathlib
from urllib.parse import quote_plus

import pandas as pd
import requests
import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

conf_dir = pathlib.Path(__file__).parent.parent / "config"
log_dir = pathlib.Path(__file__).parent.parent / "logs"
data_dir = pathlib.Path(__file__).parent.parent / "data"

os.makedirs(log_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

log_file = log_dir / "api_pipeline.log"



logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


load_dotenv(conf_dir / ".env")


def extract_data(url: str) -> dict:
    """
    Extract data from the API endpoint.

    Args:
        url (str): The API endpoint URL.
    Returns:
        dict: The extracted data.
    """

    try:

        response = requests.get(url)
        if response.status_code == 200:
            logger.info(f"Successfully extracted data from {url}")
            return response.json()
        else:
            logger.exception(f"Failed to extract data from {url}. Status code: {response.status_code}")
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.exception("Error occurred while making the API request")
        raise requests.exceptions.RequestException from e
    except Exception as e:
        logger.exception("An unexpected error occurred")
        raise Exception from e


def transform_data(data: dict) -> pd.DataFrame:
    """
    Transform the extracted data.

    Args:
        data (dict): The extracted data.
    Returns:
        pd.DataFrame: The transformed data.
    """

    try:
        current = data["current_weather"]
        df = pd.DataFrame([{"temperature": current.get("temperature"),
                            "windspeed": current.get("windspeed"),
                            "winddirection": current.get("winddirection"),
                            "observation_time": current.get("time"),
                            "latitude": data.get("latitude"),
                            "longitude": data.get("longitude")
                            }])
        df["observation_time"] = pd.to_datetime(df["observation_time"])
        logger.info("Successfully transformed data into DataFrame")
        """
        Table schema for the transformed data, to be created in the database if it doesn't exist:
        CREATE TABLE weather_data (
            id SERIAL PRIMARY KEY,
            temperature FLOAT,
            windspeed FLOAT,
            winddirection FLOAT,
            observation_time TIMESTAMP,
            latitude FLOAT,
            longitude FLOAT,
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        return df

    except Exception as e:
        logger.exception("An error occurred during data transformation")
        raise Exception from e


def load_data(df: pd.DataFrame, connection_string: str) -> None:
    """
    Load the transformed data into the database.

    Args:
        df (pd.DataFrame): The transformed data.
        connection_string (str): The database connection string.
    """

    try:
        engine = create_engine(connection_string)
        df['inserted_at'] = pd.Timestamp.now()
        df.to_sql("weather_data", con=engine, if_exists="append", index=False)
        logger.info("Successfully loaded data into the database")
    except sqlalchemy.exc.SQLAlchemyError as e:
        logger.exception("Database error occurred while loading data")
        raise sqlalchemy.exc.SQLAlchemyError from e
    except Exception as e:
        logger.exception("An error occurred while loading data into the database")
        raise Exception from e


def run_pipeline(url: str, connection_string: str) -> None:
    """
    Run the ETL pipeline.

    Args:
        url (str): The API endpoint URL.
        connection_string (str): The database connection string.
    Returns:
        None
    """

    data = extract_data(url)
    df = transform_data(data)
    load_data(df, connection_string)
    logger.info("ETL pipeline completed successfully")
    


if __name__ == "__main__":
    api_url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true"
    
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    db_user = quote_plus(db_user)
    db_password = quote_plus(db_password)

    db_connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    run_pipeline(api_url, db_connection_string)
    