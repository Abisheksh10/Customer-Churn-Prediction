import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


# --------------------------------------------------
# Database connection
# --------------------------------------------------

DATABASE_URL = (
    "mysql+pymysql://root:root@localhost:3306/telecom"
)

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# Load CSV
# --------------------------------------------------

csv_file = "telecom_churn.csv"

logging.info("Loading CSV: %s", csv_file)

df = pd.read_csv(csv_file)

logging.info("CSV rows: %d", len(df))


# --------------------------------------------------
# Load into staging table
# --------------------------------------------------

df.to_sql(
    name="stg_customer_raw",
    con=engine,
    if_exists="append",
    index=False
)

logging.info(
    "CSV loaded into stg_customer_raw successfully"
)

