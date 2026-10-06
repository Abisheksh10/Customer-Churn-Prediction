import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

from predict import predict_churn


# =========================================================
# DATABASE CONNECTION
# =========================================================

engine = create_engine(
    "mysql+pymysql://root:root@localhost/telecom"
)


# =========================================================
# LOAD CUSTOMER DATA
# =========================================================

print("=" * 60)
print("ML5 BATCH CHURN SCORING")
print("=" * 60)

print("\nLoading customer_ml_features...")

df = pd.read_sql(
    "SELECT * FROM customer_ml_features",
    engine
)

print(f"Rows loaded: {len(df)}")


# =========================================================
# CHECK REQUIRED COLUMNS
# =========================================================

required_columns = [
    "customer_id",
    "tenure",
    "monthly_charges",
    "contract",
    "service_count"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# =========================================================
# 273-274. APPLY MODEL TO EVERY CUSTOMER
# =========================================================

print("\nScoring customers...")

def score_customer(row):

    result = predict_churn(
        tenure=row["tenure"],
        monthly_charges=row["monthly_charges"],
        contract_type=row["contract"],
        service_count=row["service_count"]
    )

    return pd.Series({
        "risk_score": result["risk_score"],
        "prediction": result["prediction"],
        "confidence": result["confidence"]
    })


# Apply prediction row by row
scores = df.apply(
    score_customer,
    axis=1
)


# =========================================================
# ADD RESULTS
# =========================================================

df["risk_score"] = scores["risk_score"]
df["prediction"] = scores["prediction"]
df["confidence"] = scores["confidence"]


# =========================================================
# 275. SCORING DATE
# =========================================================

df["scoring_date"] = datetime.today().strftime(
    "%Y-%m-%d"
)


# =========================================================
# 276. CREATE FINAL RISK TABLE
# =========================================================

customer_risk_table = df[
    [
        "customer_id",
        "risk_score",
        "prediction",
        "confidence",
        "scoring_date"
    ]
].copy()


print("\nCustomer risk table created.")

print(
    f"Rows in risk table: {len(customer_risk_table)}"
)


# =========================================================
# SAVE TO MYSQL
# =========================================================

print("\nSaving customer_risk_table to MySQL...")

customer_risk_table.to_sql(
    "customer_risk_table",
    engine,
    if_exists="replace",
    index=False
)

print("customer_risk_table saved successfully.")


# =========================================================
# 277. PREDICTION DISTRIBUTION
# =========================================================

print("\n" + "=" * 60)
print("PREDICTED CHURN DISTRIBUTION")
print("=" * 60)

prediction_counts = (
    customer_risk_table["prediction"]
    .value_counts()
)

print(prediction_counts)


print("\nPrediction percentages:")

prediction_percentages = (
    customer_risk_table["prediction"]
    .value_counts(normalize=True) * 100
)

print(prediction_percentages.round(2))


# =========================================================
# TOP 10 HIGH-RISK CUSTOMERS
# =========================================================

print("\n" + "=" * 60)
print("TOP 10 HIGHEST-RISK CUSTOMERS")
print("=" * 60)

top_10 = (
    customer_risk_table
    .sort_values(
        "risk_score",
        ascending=False
    )
    .head(10)
)

print(
    top_10.to_string(index=False)
)


# =========================================================
# SAVE TOP 10
# =========================================================

top_10.to_csv(
    "top10_ml_risk_customers.csv",
    index=False
)

print(
    "\nTop 10 saved to "
    "top10_ml_risk_customers.csv"
)


# =========================================================
# VERIFY ROW COUNT
# =========================================================

print("\n" + "=" * 60)
print("FINAL VERIFICATION")
print("=" * 60)

print(
    f"Original customers : {len(df)}"
)

print(
    f"Risk table rows    : {len(customer_risk_table)}"
)

if len(df) == len(customer_risk_table):

    print("PASS: All customers were scored.")

else:

    print("WARNING: Row count mismatch!")


# =========================================================
# COMPLETE
# =========================================================

print("\n" + "=" * 60)
print("ML5 BATCH SCORING COMPLETE")
print("=" * 60)