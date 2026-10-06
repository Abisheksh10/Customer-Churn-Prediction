import os
import shutil
import logging
import pandas as pd

from sqlalchemy import create_engine, text
from datetime import datetime


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Database connection
# --------------------------------------------------

DATABASE_URL = (
    "mysql+pymysql://root:root@localhost:3306/telecom"
)

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# Folder paths
# --------------------------------------------------

LANDING_DIR = "data/landing"
RAW_DIR = "data/raw"
REJECTED_DIR = "data/rejected"
LOG_DIR = "data/logs"


# --------------------------------------------------
# Expected CSV schema
# --------------------------------------------------

EXPECTED_COLS = [
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn"
]


# --------------------------------------------------
# Create folders
# --------------------------------------------------

def create_folders():

    os.makedirs(LANDING_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(REJECTED_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    logger.info("Folder structure ready")


# --------------------------------------------------
# 183. Detect files
# --------------------------------------------------

def detect_files():

    files = []

    for filename in os.listdir(LANDING_DIR):

        if filename.lower().endswith(".csv"):

            filepath = os.path.join(
                LANDING_DIR,
                filename
            )

            files.append(filepath)

    logger.info(
        "Detected %d CSV file(s)",
        len(files)
    )

    return files


# --------------------------------------------------
# 184. Validate schema
# --------------------------------------------------

def validate_schema(filepath):

    try:

        header = pd.read_csv(
            filepath,
            nrows=0
        ).columns.tolist()

        if header == EXPECTED_COLS:

            logger.info(
                "Schema validation passed: %s",
                filepath
            )

            return True, ""

        else:

            reason = (
                "Column mismatch. "
                f"Expected {len(EXPECTED_COLS)} columns, "
                f"found {len(header)} columns."
            )

            logger.warning(
                "Schema validation failed: %s",
                reason
            )

            return False, reason

    except Exception as e:

        reason = f"Schema validation error: {str(e)}"

        logger.error(reason)

        return False, reason


# --------------------------------------------------
# 185. Load to staging
# --------------------------------------------------

def load_to_staging(filepath, engine):

    logger.info(
        "Loading file into staging: %s",
        filepath
    )

    df = pd.read_csv(filepath)

    row_count = len(df)

    df.to_sql(
        name="stg_customer_raw",
        con=engine,
        if_exists="replace",
        index=False
    )

    logger.info(
        "Loaded %d rows into stg_customer_raw",
        row_count
    )

    return row_count


# --------------------------------------------------
# 186. Log ingestion
# --------------------------------------------------

def log_ingestion(
    filename,
    status,
    rows,
    reason
):

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                INSERT INTO ingestion_log1
                (
                    filename,
                    status,
                    row_count,
                    reason,
                    loaded_at
                )
                VALUES
                (
                    :filename,
                    :status,
                    :rows,
                    :reason,
                    :loaded_at
                )
                """
            ),
            {
                "filename": filename,
                "status": status,
                "rows": rows,
                "reason": reason,
                "loaded_at": datetime.now()
            }
        )

    logger.info(
        "Ingestion logged: %s - %s",
        filename,
        status
    )


# --------------------------------------------------
# Move valid file to raw
# --------------------------------------------------

def move_to_raw(filepath):

    filename = os.path.basename(filepath)

    destination = os.path.join(
        RAW_DIR,
        filename
    )

    shutil.move(
        filepath,
        destination
    )

    logger.info(
        "Moved file to raw: %s",
        destination
    )


# --------------------------------------------------
# Move invalid file to rejected
# --------------------------------------------------

def move_to_rejected(filepath):

    filename = os.path.basename(filepath)

    destination = os.path.join(
        REJECTED_DIR,
        filename
    )

    shutil.move(
        filepath,
        destination
    )

    logger.info(
        "Moved rejected file to: %s",
        destination
    )


# --------------------------------------------------
# 187. Process landing
# --------------------------------------------------

def process_landing():

    logger.info(
        "Starting DE2 ingestion process"
    )

    files = detect_files()

    for filepath in files:

        filename = os.path.basename(filepath)

        logger.info(
            "Processing file: %s",
            filename
        )

        # ------------------------------------------
        # Validate
        # ------------------------------------------

        valid, reason = validate_schema(filepath)

        if not valid:

            log_ingestion(
                filename=filename,
                status="REJECTED",
                rows=0,
                reason=reason
            )

            move_to_rejected(filepath)

            continue

        # ------------------------------------------
        # Load
        # ------------------------------------------

        try:

            row_count = load_to_staging(
                filepath,
                engine
            )

            log_ingestion(
                filename=filename,
                status="LOADED",
                rows=row_count,
                reason="Schema validation passed"
            )

            move_to_raw(filepath)

        except Exception as e:

            reason = f"Load failed: {str(e)}"

            logger.error(reason)

            log_ingestion(
                filename=filename,
                status="REJECTED",
                rows=0,
                reason=reason
            )

            move_to_rejected(filepath)

    logger.info(
        "DE2 ingestion process completed"
    )


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    create_folders()

    process_landing()