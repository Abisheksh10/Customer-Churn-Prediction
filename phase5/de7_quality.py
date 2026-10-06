import pandas as pd
import json
import logging


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# QUALITY CHECK 1
# ---------------------------------------------------------

def check_null_rate(df, col, threshold):
    """
    Check whether the null percentage of a column
    is within the allowed threshold.
    """

    null_count = df[col].isnull().sum()
    null_rate = (null_count / len(df)) * 100

    passed = null_rate <= threshold

    return {
        "check_name": f"Null rate check - {col}",
        "status": "PASS" if passed else "FAIL",
        "value_found": round(null_rate, 2),
        "threshold": f"<= {threshold}%",
        "severity": "CRITICAL"
    }


# ---------------------------------------------------------
# QUALITY CHECK 2
# ---------------------------------------------------------

def check_value_range(df, col, minimum, maximum):
    """
    Check whether all non-null values are inside
    the specified range.
    """

    invalid_count = (
        (df[col] < minimum) |
        (df[col] > maximum)
    ).sum()

    passed = invalid_count == 0

    return {
        "check_name": f"Value range check - {col}",
        "status": "PASS" if passed else "FAIL",
        "value_found": f"{invalid_count} invalid values",
        "threshold": f"{minimum} to {maximum}",
        "severity": "CRITICAL"
    }


# ---------------------------------------------------------
# QUALITY CHECK 3
# ---------------------------------------------------------

def check_allowed_values(df, col, allowed_set):
    """
    Check whether a column contains only allowed values.
    """

    invalid_values = df.loc[
        ~df[col].isin(allowed_set),
        col
    ].dropna().unique()

    passed = len(invalid_values) == 0

    return {
        "check_name": f"Allowed values check - {col}",
        "status": "PASS" if passed else "FAIL",
        "value_found": (
            "No invalid values"
            if passed
            else list(invalid_values)
        ),
        "threshold": list(allowed_set),
        "severity": "CRITICAL"
    }


# ---------------------------------------------------------
# QUALITY CHECK 4
# ---------------------------------------------------------

def check_row_count(df, expected_min):
    """
    Check whether the dataset contains at least
    the expected minimum number of rows.
    """

    row_count = len(df)

    passed = row_count >= expected_min

    return {
        "check_name": "Row count check",
        "status": "PASS" if passed else "FAIL",
        "value_found": row_count,
        "threshold": f">= {expected_min}",
        "severity": "CRITICAL"
    }


# ---------------------------------------------------------
# QUALITY CHECK 5
# ---------------------------------------------------------

def check_no_duplicates(df, key_col):
    """
    Check whether the key column contains duplicates.
    """

    duplicate_count = df[key_col].duplicated().sum()

    passed = duplicate_count == 0

    return {
        "check_name": f"Duplicate check - {key_col}",
        "status": "PASS" if passed else "FAIL",
        "value_found": f"{duplicate_count} duplicates",
        "threshold": "0 duplicates",
        "severity": "CRITICAL"
    }


# ---------------------------------------------------------
# QUALITY CHECK 6
# ---------------------------------------------------------

def check_churn_distribution(df):
    """
    Check whether both churn classes are present.
    This helps detect problems such as a file containing
    only churned or only non-churned customers.
    """

    churn_counts = df["Churn"].value_counts().to_dict()

    has_yes = "Yes" in churn_counts
    has_no = "No" in churn_counts

    passed = has_yes and has_no

    return {
        "check_name": "Churn distribution check",
        "status": "PASS" if passed else "FAIL",
        "value_found": churn_counts,
        "threshold": "Both Yes and No must be present",
        "severity": "WARNING"
    }


# ---------------------------------------------------------
# RUN ALL QUALITY CHECKS
# ---------------------------------------------------------

def run_quality_checks(df):

    logger.info("Starting DE7 data quality checks")

    results = []

    # 1. Null rate checks
    results.append(
        check_null_rate(
            df,
            "MonthlyCharges",
            0
        )
    )

    results.append(
        check_null_rate(
            df,
            "tenure",
            0
        )
    )

    # 2. Value range checks
    results.append(
        check_value_range(
            df,
            "tenure",
            0,
            100
        )
    )

    # MonthlyCharges must be > 0
    monthly_charges_invalid = (
        df["MonthlyCharges"] <= 0
    ).sum()

    results.append({
        "check_name": "Value range check - MonthlyCharges",
        "status": (
            "PASS"
            if monthly_charges_invalid == 0
            else "FAIL"
        ),
        "value_found": f"{monthly_charges_invalid} invalid values",
        "threshold": "> 0",
        "severity": "CRITICAL"
    })

    # 3. Allowed contract values
    results.append(
        check_allowed_values(
            df,
            "Contract",
            {
                "Month-to-month",
                "One year",
                "Two year"
            }
        )
    )

    # 4. Row count
    results.append(
        check_row_count(
            df,
            7000
        )
    )

    # 5. Duplicate customer IDs
    results.append(
        check_no_duplicates(
            df,
            "customerID"
        )
    )

    # 6. Churn distribution
    results.append(
        check_churn_distribution(df)
    )

    return results


# ---------------------------------------------------------
# PRINT QUALITY REPORT
# ---------------------------------------------------------

def print_quality_report(results):

    print()
    print("=" * 60)
    print("DE7 DATA QUALITY REPORT")
    print("=" * 60)

    for result in results:

        status = result["status"]

        print(
            f"{status} - "
            f"{result['check_name']} | "
            f"Value: {result['value_found']} | "
            f"Threshold: {result['threshold']} | "
            f"Severity: {result['severity']}"
        )

    print("=" * 60)


# ---------------------------------------------------------
# SAVE JSON REPORT
# ---------------------------------------------------------

def save_quality_report(results, filepath="quality_report.json"):

    with open(filepath, "w") as file:

        json.dump(
            results,
            file,
            indent=4,
            default=str
        )

    logger.info(
        "Quality report saved to %s",
        filepath
    )


# ---------------------------------------------------------
# HANDLE FAILURES
# ---------------------------------------------------------

def handle_quality_results(results):

    critical_failures = [
        result
        for result in results
        if result["status"] == "FAIL"
        and result["severity"] == "CRITICAL"
    ]

    warning_failures = [
        result
        for result in results
        if result["status"] == "FAIL"
        and result["severity"] == "WARNING"
    ]

    # WARNING → continue
    for warning in warning_failures:

        logger.warning(
            "WARNING: %s failed. Value: %s",
            warning["check_name"],
            warning["value_found"]
        )

    # CRITICAL → stop pipeline
    if critical_failures:

        for failure in critical_failures:

            logger.error(
                "CRITICAL CHECK FAILED: %s",
                failure["check_name"]
            )

        raise Exception(
            "DE7 quality gate failed. "
            "Pipeline execution stopped."
        )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    logger.info("DE7 quality pipeline started")

    filepath = "data/landing/telecom_churn.csv"

    try:

        # Read data
        df = pd.read_csv(filepath)

        logger.info(
            "Read %s rows from %s",
            len(df),
            filepath
        )

        # Run checks
        results = run_quality_checks(df)

        # Print report
        print_quality_report(results)

        # Save report
        save_quality_report(results)

        # Handle CRITICAL / WARNING
        handle_quality_results(results)

        logger.info(
            "DE7 quality pipeline completed successfully"
        )

    except Exception as e:

        logger.error(
            "DE7 quality pipeline failed: %s",
            e
        )

        raise


if __name__ == "__main__":
    main()