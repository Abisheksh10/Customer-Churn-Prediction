import os
import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import text

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = (
    "mysql+pymysql://root:root@localhost:3306/telecom"
)


engine = create_engine(
    DATABASE_URL
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# PROCESS INCREMENTAL DATA
# ---------------------------------------------------------

def process_incremental(filepath, engine):

    logger.info("Starting DE6 incremental pipeline")

    # Read daily customer extract
    df = pd.read_csv(filepath)

    logger.info(
        "Read %s rows from %s",
        len(df),
        filepath
    )

    rows_inserted = 0
    rows_updated = 0
    rows_unchanged = 0

    # -----------------------------------------------------
    # PROCESS EACH CUSTOMER
    # -----------------------------------------------------

    with engine.begin() as conn:

        for _, row in df.iterrows():

            customer_id = row["customerID"]

            # -------------------------------------------------
            # GET EXISTING CUSTOMER
            # -------------------------------------------------

            existing = conn.execute(
                text("""
                    SELECT
                        customer_id,
                        gender,
                        senior_citizen,
                        partner,
                        dependents
                    FROM customers1
                    WHERE customer_id = :customer_id
                """),
                {
                    "customer_id": customer_id
                }
            ).mappings().first()

            # -------------------------------------------------
            # PREPARE INCOMING DATA
            # -------------------------------------------------

            incoming = {
                "customer_id": customer_id,
                "gender": row["gender"],
                "senior_citizen": int(row["SeniorCitizen"]),
                "partner": (
                    1
                    if row["Partner"] == "Yes"
                    else 0
                ),
                "dependents": (
                    1
                    if row["Dependents"] == "Yes"
                    else 0
                )
            }

            # -------------------------------------------------
            # CASE 1: NEW CUSTOMER
            # -------------------------------------------------

            if existing is None:

                conn.execute(
                    text("""
                        INSERT INTO customers1 (
                            customer_id,
                            gender,
                            senior_citizen,
                            partner,
                            dependents
                        )
                        VALUES (
                            :customer_id,
                            :gender,
                            :senior_citizen,
                            :partner,
                            :dependents
                        )
                    """),
                    incoming
                )

                rows_inserted += 1

            # -------------------------------------------------
            # CASE 2 & 3: EXISTING CUSTOMER
            # -------------------------------------------------

            else:

                changed = (
                    existing["gender"]
                    != incoming["gender"]
                    or existing["senior_citizen"]
                    != incoming["senior_citizen"]
                    or existing["partner"]
                    != incoming["partner"]
                    or existing["dependents"]
                    != incoming["dependents"]
                )

                # ---------------------------------------------
                # CASE 3: UNCHANGED
                # ---------------------------------------------

                if not changed:

                    rows_unchanged += 1

                # ---------------------------------------------
                # CASE 2: UPDATED
                # ---------------------------------------------

                else:

                    conn.execute(
                        text("""
                            UPDATE customers1
                            SET
                                gender = :gender,
                                senior_citizen = :senior_citizen,
                                partner = :partner,
                                dependents = :dependents
                            WHERE customer_id = :customer_id
                        """),
                        incoming
                    )

                    rows_updated += 1

    # ---------------------------------------------------------
    # PRINT RESULTS
    # ---------------------------------------------------------

    logger.info("Incremental processing completed")

    logger.info(
        "Rows inserted: %s",
        rows_inserted
    )

    logger.info(
        "Rows updated: %s",
        rows_updated
    )

    logger.info(
        "Rows unchanged: %s",
        rows_unchanged
    )

    return {
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "rows_unchanged": rows_unchanged
    }


# ---------------------------------------------------------
# CREATE PIPELINE RUN LOG TABLE
# ---------------------------------------------------------

def create_pipeline_log_table(engine):

    with engine.begin() as conn:

        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS pipeline_run_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_name VARCHAR(255),
                    rows_inserted INT,
                    rows_updated INT,
                    rows_unchanged INT,
                    run_timestamp DATETIME
                )
            """)
        )

    logger.info("pipeline_run_log table ready")


# ---------------------------------------------------------
# LOG PIPELINE RUN
# ---------------------------------------------------------

def log_pipeline_run(
    engine,
    file_name,
    rows_inserted,
    rows_updated,
    rows_unchanged
):

    with engine.begin() as conn:

        conn.execute(
            text("""
                INSERT INTO pipeline_run_log (
                    file_name,
                    rows_inserted,
                    rows_updated,
                    rows_unchanged,
                    run_timestamp
                )
                VALUES (
                    :file_name,
                    :rows_inserted,
                    :rows_updated,
                    :rows_unchanged,
                    :run_timestamp
                )
            """),
            {
                "file_name": file_name,
                "rows_inserted": rows_inserted,
                "rows_updated": rows_updated,
                "rows_unchanged": rows_unchanged,
                "run_timestamp": datetime.now()
            }
        )

    logger.info("Pipeline run logged")


# ---------------------------------------------------------
# VERIFY CUSTOMER COUNT
# ---------------------------------------------------------

def get_customer_count(engine):

    with engine.connect() as conn:

        result = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM customers1
            """)
        )

        return result.scalar()


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    filepath = "data/landing/telecom_churn.csv"

    try:

        logger.info("DE6 incremental processing started")

        # Make sure pipeline log table exists
        create_pipeline_log_table(engine)

        # Get count before processing
        count_before = get_customer_count(engine)

        logger.info(
            "customers1 count before processing: %s",
            count_before
        )

        # Process daily extract
        result = process_incremental(
            filepath,
            engine
        )

        # Get count after processing
        count_after = get_customer_count(engine)

        logger.info(
            "customers1 count after processing: %s",
            count_after
        )

        # Log pipeline run
        log_pipeline_run(
            engine=engine,
            file_name=os.path.basename(filepath),
            rows_inserted=result["rows_inserted"],
            rows_updated=result["rows_updated"],
            rows_unchanged=result["rows_unchanged"]
        )

        # -------------------------------------------------
        # FINAL SUMMARY
        # -------------------------------------------------

        print("\n" + "=" * 50)
        print("DE6 INCREMENTAL PROCESSING SUMMARY")
        print("=" * 50)

        print(
            f"Rows inserted   : {result['rows_inserted']}"
        )

        print(
            f"Rows updated    : {result['rows_updated']}"
        )

        print(
            f"Rows unchanged  : {result['rows_unchanged']}"
        )

        print(
            f"Count before    : {count_before}"
        )

        print(
            f"Count after     : {count_after}"
        )

        print("=" * 50)

        logger.info(
            "DE6 incremental pipeline completed successfully"
        )

    except Exception as e:

        logger.error(
            "DE6 pipeline failed: %s",
            e,
            exc_info=True
        )

        raise


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    main()