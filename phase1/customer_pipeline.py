#task 5



import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

from customer_cleaner import CustomerCleaner


# --------------------------------------------------
# Logging configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# --------------------------------------------------
# Load data
# --------------------------------------------------

def load_data(filepath):
    logging.info("Loading data from: %s", filepath)

    df = pd.read_csv(filepath)

    logging.info("Data loaded successfully. Rows: %d", len(df))

    return df


# --------------------------------------------------
# Build features
# --------------------------------------------------

def build_features(df):

    logging.info("Starting feature engineering")

    # Feature 1: tenure_bucket
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

    logging.info("Feature 1 created: tenure_bucket")


    # Feature 2: high_charge_flag
    median_charge = df["monthly_charges"].median()

    df["high_charge_flag"] = (
        df["monthly_charges"] > median_charge
    ).astype(int)

    logging.info("Feature 2 created: high_charge_flag")


    # Service columns
    service_columns = [
        "online_security",
        "online_backup",
        "device_protection",
        "tech_support",
        "streaming_tv",
        "streaming_movies"
    ]

    # Convert service values to 1/0
    df[service_columns] = df[service_columns].replace({
        "Yes": 1,
        "No": 0,
        "No internet service": 0
    })


    # Feature 3: service_count
    df["service_count"] = (
        df[service_columns]
        .eq(1)
        .sum(axis=1)
    )

    logging.info("Feature 3 created: service_count")


    # Feature 4: is_long_term_customer
    df["is_long_term_customer"] = (
        df["tenure"] >= 24
    ).astype(int)

    logging.info(
        "Feature 4 created: is_long_term_customer"
    )


    # Feature 5: has_streaming_bundle
    df["has_streaming_bundle"] = (
        (df["streaming_tv"] == 1)
        &
        (df["streaming_movies"] == 1)
    ).astype(int)

    logging.info(
        "Feature 5 created: has_streaming_bundle"
    )


    # Feature 6: auto_pay_flag
    df["auto_pay_flag"] = (
        df["payment_method"]
        .str.contains(
            "automatic",
            case=False,
            na=False
        )
    ).astype(int)

    logging.info(
        "Feature 6 created: auto_pay_flag"
    )


    logging.info(
        "Feature engineering completed. Rows: %d",
        len(df)
    )

    return df


# --------------------------------------------------
# Save outputs
# --------------------------------------------------

def save_outputs(clean_df, feature_df, output_dir):

    logging.info("Starting output saving")

    output_path = Path(output_dir)

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


    # Cleaned data file
    clean_file = (
        output_path /
        f"customer_cleaned_{timestamp}.csv"
    )

    clean_df.to_csv(
        clean_file,
        index=False
    )


    # Feature data file
    feature_file = (
        output_path /
        f"customer_features_{timestamp}.csv"
    )

    feature_df.to_csv(
        feature_file,
        index=False
    )


    logging.info(
        "Cleaned data saved to: %s",
        clean_file
    )

    logging.info(
        "Feature data saved to: %s",
        feature_file
    )

    return clean_file, feature_file


# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def main():

    start_time = datetime.now()

    logging.info(
        "Customer pipeline started at: %s",
        start_time
    )


    # ----------------------------------------------
    # Step 1: Load
    # ----------------------------------------------

    try:

        df = load_data(
            "telecom_churn.csv"
        )

    except Exception as e:

        logging.error(
            "Loading failed: %s",
            e
        )

        raise


    # ----------------------------------------------
    # Step 2: Clean
    # ----------------------------------------------

    try:

        logging.info("Starting data cleaning")

        cleaner = CustomerCleaner(df)

        clean_df = cleaner.clean()

        logging.info(
            "Data cleaning completed. Rows: %d",
            len(clean_df)
        )

    except Exception as e:

        logging.error(
            "Cleaning failed: %s",
            e
        )

        raise


    # ----------------------------------------------
    # Step 3: Feature engineering
    # ----------------------------------------------

    try:

        feature_df = build_features(
            clean_df.copy()
        )

    except Exception as e:

        logging.error(
            "Feature engineering failed: %s",
            e
        )

        raise


    # ----------------------------------------------
    # Step 4: Data quality checks
    # ----------------------------------------------

    try:

        logging.info("Running data quality checks")

        assert (
            feature_df["monthly_charges"]
            .isna()
            .sum()
            == 0
        ), "monthly_charges contains null values"

        assert set(
            feature_df["churn"].dropna().unique()
        ).issubset({0, 1}), (
            "churn contains values other than 0/1"
        )

        logging.info(
            "Data quality checks passed"
        )

    except Exception as e:

        logging.error(
            "Data quality check failed: %s",
            e
        )

        raise


    # ----------------------------------------------
    # Step 5: Save outputs
    # ----------------------------------------------

    try:

        save_outputs(
            clean_df,
            feature_df,
            "output"
        )

    except Exception as e:

        logging.error(
            "Saving outputs failed: %s",
            e
        )

        raise


    # ----------------------------------------------
    # Pipeline completed
    # ----------------------------------------------

    end_time = datetime.now()

    logging.info(
        "Customer pipeline completed at: %s",
        end_time
    )

    logging.info(
        "Total execution time: %s",
        end_time - start_time
    )


# --------------------------------------------------
# Execute pipeline
# --------------------------------------------------

if __name__ == "__main__":
    main()