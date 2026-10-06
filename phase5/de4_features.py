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
# Build Features
# --------------------------------------------------

def build_features(engine):

    logging.info(
        "Starting feature engineering stage"
    )

    # --------------------------------------------------
    # Read cleaned data
    # --------------------------------------------------

    df = pd.read_sql(
        "SELECT * FROM cleaned_customers",
        engine
    )

    logging.info(
        "Read %d rows from cleaned_customers",
        len(df)
    )


    # --------------------------------------------------
    # Feature 1 - tenure_bucket
    # --------------------------------------------------

    df["tenure_bucket"] = pd.cut(
        df["tenure"],
        bins=[0, 12, 24, 48, 72],
        labels=[
            "0-12",
            "13-24",
            "25-48",
            "49-72"
        ],
        include_lowest=True
    )
    df["tenure_bucket"] = (
    df["tenure_bucket"]
    .astype("object")
    .fillna("Unknown")
)


    # --------------------------------------------------
    # Feature 2 - high_charge_flag
    # --------------------------------------------------

    median_charge = (
        df["monthly_charges"].median()
    )

    logging.info(
        "Monthly charges median: %.2f",
        median_charge
    )

    df["high_charge_flag"] = (
        df["monthly_charges"] > median_charge
    ).astype(int)


    # --------------------------------------------------
    # Feature 3 - service_count
    # --------------------------------------------------

    service_columns = [
        "online_security",
        "online_backup",
        "device_protection",
        "tech_support",
        "streaming_tv",
        "streaming_movies"
    ]

    df[service_columns] = (
        df[service_columns]
        .replace({
            "Yes": 1,
            "No": 0
        })
    )

    df["service_count"] = (
        df[service_columns]
        .sum(axis=1)
    )


    # --------------------------------------------------
    # Feature 4 - is_long_term_customer
    # --------------------------------------------------

    df["is_long_term_customer"] = (
        df["tenure"] >= 24
    ).astype(int)


    # --------------------------------------------------
    # Feature 5 - has_streaming_bundle
    # --------------------------------------------------

    df["has_streaming_bundle"] = (
        (df["streaming_tv"] == 1)
        &
        (df["streaming_movies"] == 1)
    ).astype(int)


    # --------------------------------------------------
    # Feature 6 - auto_pay_flag
    # --------------------------------------------------

    df["auto_pay_flag"] = (
        df["payment_method"]
        .str.contains(
            "automatic",
            case=False,
            na=False
        )
    ).astype(int)


    logging.info(
        "All 6 features created"
    )


    # --------------------------------------------------
    # Select ML columns
    # --------------------------------------------------

    feature_df = df[
        [
            "customer_id",
            "contract",
            "tenure",
            "tenure_bucket",
            "high_charge_flag",
            "service_count",
            "internet_service",
            "is_long_term_customer",
            "has_streaming_bundle",
            "auto_pay_flag",
            "monthly_charges",
            "total_charges",
            "churn"
        ]
    ].copy()


    # --------------------------------------------------
    # Write feature table
    # --------------------------------------------------

    feature_df.to_sql(
        name="customer_ml_features",
        con=engine,
        if_exists="replace",
        index=False
    )

    logging.info(
        "customer_ml_features table populated"
    )


    return feature_df


# --------------------------------------------------
# Validation 198
# --------------------------------------------------

def validate_row_count(engine):

    with engine.connect() as conn:

        cleaned_count = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM cleaned_customers
                """
            )
        ).scalar()

        feature_count = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM customer_ml_features
                """
            )
        ).scalar()


    print("\nROW COUNT VALIDATION")

    print(
        f"cleaned_customers: {cleaned_count}"
    )

    print(
        f"customer_ml_features: {feature_count}"
    )


    assert cleaned_count == feature_count, (
        "FAIL: Row count mismatch"
    )


    print(
        f"PASS: Row counts match ({feature_count})"
    )


# --------------------------------------------------
# Schema + NULL validation 199
# --------------------------------------------------

def validate_features(engine):

    required_features = [
        "tenure_bucket",
        "high_charge_flag",
        "service_count",
        "is_long_term_customer",
        "has_streaming_bundle",
        "auto_pay_flag"
    ]


    with engine.connect() as conn:

        # Get table columns
        result = conn.execute(
            text(
                """
                DESCRIBE customer_ml_features
                """
            )
        )

        columns = [
            row[0]
            for row in result
        ]


        print("\nSCHEMA VALIDATION")

        for feature in required_features:

            if feature in columns:

                print(
                    f"PASS - {feature} exists"
                )

            else:

                print(
                    f"FAIL - {feature} missing"
                )

                raise AssertionError(
                    f"Missing feature: {feature}"
                )


        # NULL checks
        for feature in required_features:

            null_count = conn.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM customer_ml_features
                    WHERE `{feature}` IS NULL
                    """
                )
            ).scalar()


            if null_count == 0:

                print(
                    f"PASS - {feature} NULL check: 0"
                )

            else:

                print(
                    f"FAIL - {feature} NULL check: "
                    f"{null_count}"
                )

                raise AssertionError(
                    f"{feature} contains NULL values"
                )


# --------------------------------------------------
# Spot check 3 customers
# --------------------------------------------------

def spot_check(engine):

    with engine.connect() as conn:

        result = conn.execute(
            text(
                """
                SELECT
                    customer_id,
                    tenure_bucket,
                    high_charge_flag,
                    service_count,
                    is_long_term_customer,
                    has_streaming_bundle,
                    auto_pay_flag,
                    monthly_charges,
                    total_charges,
                    churn
                FROM customer_ml_features
                LIMIT 3
                """
            )
        )

        rows = result.fetchall()


    print("\nSPOT CHECK - 3 CUSTOMERS")

    for row in rows:

        print(
            f"\nCustomer ID: {row.customer_id}"
        )

        print(
            f"tenure_bucket: "
            f"{row.tenure_bucket}"
        )

        print(
            f"high_charge_flag: "
            f"{row.high_charge_flag}"
        )

        print(
            f"service_count: "
            f"{row.service_count}"
        )

        print(
            f"is_long_term_customer: "
            f"{row.is_long_term_customer}"
        )

        print(
            f"has_streaming_bundle: "
            f"{row.has_streaming_bundle}"
        )

        print(
            f"auto_pay_flag: "
            f"{row.auto_pay_flag}"
        )

        print(
            f"monthly_charges: "
            f"{row.monthly_charges}"
        )

        print(
            f"total_charges: "
            f"{row.total_charges}"
        )

        print(
            f"churn: {row.churn}"
        )


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    logging.info(
        "DE4 feature pipeline started"
    )

    try:

        # 196 + 197
        build_features(engine)

        # 198
        validate_row_count(engine)

        # 199
        validate_features(engine)

        # 200
        spot_check(engine)

        logging.info(
            "DE4 feature pipeline completed successfully"
        )

    except Exception as e:

        logging.error(
            "DE4 feature pipeline failed: %s",
            e
        )

        raise


if __name__ == "__main__":
    main()