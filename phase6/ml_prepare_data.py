import pandas as pd
from sqlalchemy import create_engine


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

engine = create_engine(
    "mysql+pymysql://root:root@localhost/telecom"
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

print("Loading customer_ml_features...")

df = pd.read_sql(
    "SELECT * FROM customer_ml_features",
    engine
)

print(f"Rows loaded: {len(df)}")


# ---------------------------------------------------------
# DISPLAY COLUMNS
# ---------------------------------------------------------

print("\nALL COLUMNS")
print("=" * 50)

print(df.columns.tolist())


# ---------------------------------------------------------
# TARGET
# ---------------------------------------------------------

target = "churn"

print("\nTARGET COLUMN")
print("=" * 50)

print(f"Target: {target}")


# ---------------------------------------------------------
# DROP IDENTIFIER
# ---------------------------------------------------------

drop_columns = ["customer_id"]

print("\nDROP COLUMNS")
print("=" * 50)

print(drop_columns)


# ---------------------------------------------------------
# NUMERIC FEATURES
# ---------------------------------------------------------

numeric_columns = [
    "tenure",
    "monthly_charges",
    "total_charges",
    "service_count",
    "high_charge_flag",
    "is_long_term_customer",
    "auto_pay_flag",
    "has_streaming_bundle"
]

print("\nNUMERIC FEATURES")
print("=" * 50)

for column in numeric_columns:
    print(column)


# ---------------------------------------------------------
# CATEGORICAL FEATURES
# ---------------------------------------------------------

categorical_columns = [
    "contract",
    "internet_service"
]

print("\nCATEGORICAL FEATURES")
print("=" * 50)

for column in categorical_columns:
    print(column)


# ---------------------------------------------------------
# CHECK REQUIRED COLUMNS
# ---------------------------------------------------------

required_columns = (
    numeric_columns
    + categorical_columns
    + [target]
    + drop_columns
)

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ---------------------------------------------------------
# CREATE X AND y
# ---------------------------------------------------------

X = df[
    numeric_columns + categorical_columns
].copy()

y = df[target].copy()


# ---------------------------------------------------------
# ONE-HOT ENCODING
# ---------------------------------------------------------

X = pd.get_dummies(
    X,
    columns=categorical_columns,
    drop_first=False,
    dtype=int
)


# ---------------------------------------------------------
# FINAL FEATURE SET
# ---------------------------------------------------------

print("\nFINAL FEATURE MATRIX X")
print("=" * 50)

print(X)


print("\nFINAL FEATURE COLUMNS")
print("=" * 50)

print(X.columns.tolist())


# ---------------------------------------------------------
# TARGET
# ---------------------------------------------------------

print("\nTARGET y")
print("=" * 50)

print(y)


# ---------------------------------------------------------
# SHAPES
# ---------------------------------------------------------

print("\nSHAPES")
print("=" * 50)

print("X.shape:", X.shape)
print("y.shape:", y.shape)


# ---------------------------------------------------------
# CLASS BALANCE
# ---------------------------------------------------------

print("\nCLASS BALANCE")
print("=" * 50)

print(y.value_counts())

print("\nCLASS BALANCE (%)")

print(
    y.value_counts(normalize=True)
)


# ---------------------------------------------------------
# FINAL SUMMARY
# ---------------------------------------------------------

print("\nML1 DATA PREPARATION COMPLETE")
print("=" * 50)

print(f"Total customers : {len(df)}")
print(f"Features        : {X.shape[1]}")
print(f"Target          : {target}")
print(f"X shape         : {X.shape}")
print(f"y shape         : {y.shape}")