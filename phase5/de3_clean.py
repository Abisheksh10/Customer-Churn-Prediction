import pandas as pd
import logging

from sqlalchemy import create_engine, text

from customer_cleaner import CustomerCleaner


# --------------------------------------------------
# Logging
# --------------------------------------------------

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
# Step 190
# Read staging -> clean -> cleaned_customers
# --------------------------------------------------

def clean_staging(engine):

    logging.info("Starting cleaning stage")

    # Read raw staging table
    df = pd.read_sql(
        "SELECT * FROM stg_customer_raw",
        engine
    )

    logging.info(
        "Read %d rows from stg_customer_raw",
        len(df)
    )

    # Clean using Phase 1 CustomerCleaner
    cleaner = CustomerCleaner(df)

    clean_df = cleaner.clean()

    logging.info(
        "Cleaning completed: %d rows",
        len(clean_df)
    )

    # Write cleaned data
    clean_df.to_sql(
        name="cleaned_customers",
        con=engine,
        if_exists="replace",
        index=False
    )

    logging.info(
        "cleaned_customers table created"
    )

    return clean_df


# --------------------------------------------------
# Step 192
# Row count check
# --------------------------------------------------

def check_row_count(engine):

    with engine.connect() as conn:

        staging_count = conn.execute(
            text(
                "SELECT COUNT(*) "
                "FROM stg_customer_raw"
            )
        ).scalar()

        cleaned_count = conn.execute(
            text(
                "SELECT COUNT(*) "
                "FROM cleaned_customers"
            )
        ).scalar()

    print("\nROW COUNT CHECK")

    print(
        f"stg_customer_raw: {staging_count}"
    )

    print(
        f"cleaned_customers: {cleaned_count}"
    )

    assert staging_count == cleaned_count, (
        "FAIL: Row count mismatch"
    )

    print(
        f"PASS: Row counts match ({cleaned_count})"
    )


# --------------------------------------------------
# Step 193 + 194
# Data quality checks
# --------------------------------------------------

def quality_checks(engine):

    with engine.connect() as conn:

        # Check customer_id NULLs
        null_customer_id = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM cleaned_customers
                WHERE customer_id IS NULL
                """
            )
        ).scalar()

        # Check monthly_charges NULLs
        null_monthly_charges = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM cleaned_customers
                WHERE monthly_charges IS NULL
                """
            )
        ).scalar()

        # Check invalid churn values
        invalid_churn = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM cleaned_customers
                WHERE churn NOT IN (0, 1)
                """
            )
        ).scalar()


    print("\nDATA QUALITY REPORT")

    # customer_id
    if null_customer_id == 0:
        print(
            "PASS - customer_id NULL check: 0"
        )
    else:
        print(
            f"FAIL - customer_id NULL check: "
            f"{null_customer_id}"
        )

    # monthly_charges
    if null_monthly_charges == 0:
        print(
            "PASS - monthly_charges NULL check: 0"
        )
    else:
        print(
            f"FAIL - monthly_charges NULL check: "
            f"{null_monthly_charges}"
        )

    # churn
    if invalid_churn == 0:
        print(
            "PASS - churn values check: 0 invalid"
        )
    else:
        print(
            f"FAIL - churn values check: "
            f"{invalid_churn} invalid"
        )

    # Fail pipeline if any check fails
    assert null_customer_id == 0, (
        "customer_id contains NULL values"
    )

    assert null_monthly_charges == 0, (
        "monthly_charges contains NULL values"
    )

    assert invalid_churn == 0, (
        "churn contains invalid values"
    )


# --------------------------------------------------
# Step 191
# Build curated tables
# --------------------------------------------------

def build_curated_tables(engine):

    logging.info(
        "Building curated tables"
    )

    with engine.begin() as conn:

        # --------------------------------------------------
        # Clear existing curated data
        # --------------------------------------------------
        # Delete fact table first because it contains
        # foreign keys referencing other tables.

        conn.execute(
            text(
                "DELETE FROM fact_customer_account"
            )
        )

        conn.execute(
            text(
                "DELETE FROM customers1"
            )
        )

        conn.execute(
            text(
                "DELETE FROM dim_payment"
            )
        )

        conn.execute(
            text(
                "DELETE FROM dim_contract"
            )
        )

        logging.info(
            "Existing curated data cleared"
        )


        # --------------------------------------------------
        # dim_contract
        # --------------------------------------------------

        conn.execute(
            text(
                """
                INSERT INTO dim_contract
                (
                    contract_name
                )

                SELECT DISTINCT
                    contract

                FROM cleaned_customers

                WHERE contract IS NOT NULL
                """
            )
        )

        logging.info(
            "dim_contract populated"
        )


        # --------------------------------------------------
        # dim_payment
        # --------------------------------------------------

        conn.execute(
            text(
                """
                INSERT INTO dim_payment
                (
                    payment_method
                )

                SELECT DISTINCT
                    payment_method

                FROM cleaned_customers

                WHERE payment_method IS NOT NULL
                """
            )
        )

        logging.info(
            "dim_payment populated"
        )


        # --------------------------------------------------
        # customers1
        # --------------------------------------------------

        conn.execute(
            text(
                """
                INSERT INTO customers1
                (
                    customer_id,
                    gender,
                    senior_citizen,
                    partner,
                    dependents
                )

                SELECT

                    customer_id,

                    CASE
                        WHEN LOWER(gender) = 'male'
                        THEN 'Male'

                        WHEN LOWER(gender) = 'female'
                        THEN 'Female'

                        ELSE gender
                    END,

                    CAST(
                        senior_citizen
                        AS UNSIGNED
                    ),

                    CASE
                        WHEN LOWER(partner) = 'yes'
                        THEN 1
                        ELSE 0
                    END,

                    CASE
                        WHEN LOWER(dependents) = 'yes'
                        THEN 1
                        ELSE 0
                    END

                FROM cleaned_customers
                """
            )
        )

        logging.info(
            "customers1 populated"
        )


        # --------------------------------------------------
        # fact_customer_account
        # --------------------------------------------------

        conn.execute(
            text(
                """
                INSERT INTO fact_customer_account
                (
                    customer_id,
                    contract_id,
                    payment_id,
                    tenure,
                    internet_service,
                    monthly_charges,
                    total_charges,
                    churn
                )

                SELECT

                    c.customer_id,

                    dc.contract_id,

                    dp.payment_id,

                    c.tenure,

                    c.internet_service,

                    c.monthly_charges,

                    c.total_charges,

                    c.churn

                FROM cleaned_customers c

                JOIN dim_contract dc
                    ON c.contract = dc.contract_name

                JOIN dim_payment dp
                    ON c.payment_method
                    = dp.payment_method
                """
            )
        )

        logging.info(
            "fact_customer_account populated"
        )

# --------------------------------------------------
# Verify curated tables
# --------------------------------------------------

def verify_curated_tables(engine):

    tables = [
        "dim_contract",
        "dim_payment",
        "customers1",
        "fact_customer_account"
    ]

    print("\nCURATED TABLE COUNTS")

    with engine.connect() as conn:

        for table in tables:

            count = conn.execute(
                text(
                    f"SELECT COUNT(*) FROM {table}"
                )
            ).scalar()

            print(
                f"{table}: {count}"
            )


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    logging.info(
        "DE3 cleaning pipeline started"
    )

    try:

        # 190
        clean_staging(engine)

        # 192
        check_row_count(engine)

        # 193 + 194
        quality_checks(engine)

        # 191
        build_curated_tables(engine)

        # Verify output
        verify_curated_tables(engine)

        logging.info(
            "DE3 cleaning pipeline completed successfully"
        )

    except Exception as e:

        logging.error(
            "DE3 pipeline failed: %s",
            e
        )

        raise


if __name__ == "__main__":
    main()