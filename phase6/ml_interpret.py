import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine


# =========================================================
# DATABASE CONNECTION
# =========================================================

engine = create_engine(
    "mysql+pymysql://root:root@localhost/telecom"
)


# =========================================================
# CONFIGURATION
# =========================================================

MODEL_PATH = "models/tree_churn.pkl"

# Change this if Decision Tree was selected as the best model
MODEL_NAME = "Decision Tree"


# =========================================================
# LOAD MODEL
# =========================================================

print("=" * 60)
print("ML3 MODEL INTERPRETATION")
print("=" * 60)

print(f"\nLoading best model: {MODEL_NAME}")
print(f"Model path: {MODEL_PATH}")

model = joblib.load(MODEL_PATH)

print("Model loaded successfully.")


# =========================================================
# LOAD DATA
# =========================================================

print("\nLoading customer data...")

df = pd.read_sql(
    "SELECT * FROM customer_ml_features",
    engine
)

print(f"Rows loaded: {len(df)}")


# =========================================================
# PREPARE FEATURES
# =========================================================

target = "churn"
id_column = "customer_id"

# These are the categorical columns in your actual table
categorical_columns = [
    "contract",
    "internet_service"
]

# Remove ID and target
X = df.drop(
    columns=[id_column, target]
)

y = df[target]


# =========================================================
# ONE-HOT ENCODING
# =========================================================

X = pd.get_dummies(
    X,
    columns=categorical_columns,
    drop_first=False
)


# =========================================================
# IMPORTANT:
# MAKE SURE FEATURES MATCH THE TRAINING MODEL
# =========================================================

if hasattr(model, "feature_names_in_"):

    expected_features = model.feature_names_in_

    print("\nChecking model feature schema...")

    missing_features = [
        col for col in expected_features
        if col not in X.columns
    ]

    extra_features = [
        col for col in X.columns
        if col not in expected_features
    ]

    if missing_features:
        print("Missing features:")
        print(missing_features)

        raise ValueError(
            f"Features used during training are missing: "
            f"{missing_features}"
        )

    # Keep exactly the columns used during training
    X = X[expected_features]

    print("Feature schema matches the trained model.")


# Convert boolean columns to integers
X = X.astype(int)


print("\nFinal feature shape:")
print(X.shape)


# =========================================================
# 255-257. MODEL INTERPRETATION
# =========================================================

print("\n" + "=" * 60)
print("FEATURE IMPORTANCE")
print("=" * 60)


if hasattr(model, "coef_"):

    # -----------------------------------------------------
    # LOGISTIC REGRESSION
    # -----------------------------------------------------

    coefficients = pd.Series(
        model.coef_[0],
        index=X.columns
    )

    # Sort by absolute coefficient
    importance = (
        coefficients
        .abs()
        .sort_values(ascending=False)
    )

    top_10_features = importance.head(10)

    print("\nTOP 10 FEATURES BY ABSOLUTE COEFFICIENT")
    print("-" * 60)

    for feature in top_10_features.index:

        coefficient = coefficients[feature]

        direction = (
            "Higher churn"
            if coefficient > 0
            else "Lower churn"
        )

        print(
            f"{feature:35s} "
            f"{coefficient:10.4f} "
            f"({direction})"
        )


    # -----------------------------------------------------
    # PLOT
    # -----------------------------------------------------

    plt.figure(figsize=(10, 6))

    plot_values = coefficients.loc[
        top_10_features.index
    ].sort_values()

    plt.barh(
        plot_values.index,
        plot_values.values
    )

    plt.axvline(
        x=0,
        linewidth=1
    )

    plt.title(
        "Top 10 Churn Drivers - Logistic Regression"
    )

    plt.xlabel(
        "Coefficient"
    )

    plt.tight_layout()

    os.makedirs("outputs", exist_ok=True)

    plt.savefig(
        "outputs/top10_churn_features.png"
    )

    plt.show()


elif hasattr(model, "feature_importances_"):

    # -----------------------------------------------------
    # DECISION TREE
    # -----------------------------------------------------

    importances = pd.Series(
        model.feature_importances_,
        index=X.columns
    )

    top_10_features = (
        importances
        .sort_values(ascending=False)
        .head(10)
    )

    print("\nTOP 10 FEATURES BY TREE IMPORTANCE")
    print("-" * 60)

    print(top_10_features)


    # -----------------------------------------------------
    # PLOT
    # -----------------------------------------------------

    plt.figure(figsize=(10, 6))

    top_10_features.sort_values().plot(
        kind="barh"
    )

    plt.title(
        "Top 10 Churn Drivers - Decision Tree"
    )

    plt.xlabel(
        "Feature Importance"
    )

    plt.tight_layout()

    os.makedirs("outputs", exist_ok=True)

    plt.savefig(
        "outputs/top10_churn_features.png"
    )

    plt.show()


else:

    raise ValueError(
        "Model does not have coef_ or feature_importances_."
    )


# =========================================================
# 258. TOP 3 CHURN DRIVERS
# =========================================================

print("\n" + "=" * 60)
print("TOP 3 CHURN DRIVERS")
print("=" * 60)


if hasattr(model, "coef_"):

    top_3 = (
        coefficients
        .abs()
        .sort_values(ascending=False)
        .head(3)
    )

    for i, feature in enumerate(top_3.index, start=1):

        coefficient = coefficients[feature]

        direction = (
            "increases churn probability"
            if coefficient > 0
            else "decreases churn probability"
        )

        print(
            f"{i}. {feature} "
            f"(coefficient={coefficient:.4f}) "
            f"-> {direction}"
        )

else:

    top_3 = (
        importances
        .sort_values(ascending=False)
        .head(3)
    )

    for i, feature in enumerate(top_3.index, start=1):

        print(
            f"{i}. {feature} "
            f"(importance={top_3[feature]:.4f})"
        )


# =========================================================
# 259. SCORE ALL CUSTOMERS
# =========================================================

print("\n" + "=" * 60)
print("CUSTOMER CHURN RISK SCORING")
print("=" * 60)

probabilities = model.predict_proba(X)[:, 1]

risk_df = pd.DataFrame({
    "customer_id": df[id_column],
    "churn_probability": probabilities
})
print(f"Customers scored: {len(risk_df)}")

print("\nRisk scoring completed successfully.")

# =========================================================
# 260. TOP 20 HIGH-RISK CUSTOMERS
# =========================================================

top_20 = (
    risk_df
    .sort_values(
        "churn_probability",
        ascending=False
    )
    .head(20)
)

print("\nTOP 20 HIGHEST-RISK CUSTOMERS")
print("-" * 60)

display_top20 = top_20.copy()

display_top20["risk_score"] = (
    display_top20["churn_probability"] * 100
).round(2)

display_top20 = display_top20[
    ["customer_id", "risk_score"]
]

print(display_top20.to_string(index=False))


# =========================================================
# SAVE TOP 20
# =========================================================

os.makedirs("outputs", exist_ok=True)

top_20.to_csv(
    "outputs/top20_ml_risk_customers.csv",
    index=False
)

print(
    "\nTop 20 customers saved to "
    "outputs/top20_ml_risk_customers.csv"
)


# =========================================================
# 261. COMPARE WITH SQL6 HIGH-RISK CUSTOMERS
# =========================================================

print("\n" + "=" * 60)
print("ML RISK VS SQL6 RULE-BASED RISK")
print("=" * 60)


# ---------------------------------------------------------
# Try to find the SQL6 high-risk table
# ---------------------------------------------------------

possible_tables = [
    "high_risk_customers",
    "high_risk_customers1"
]

sql6_table = None

for table in possible_tables:

    try:

        test_df = pd.read_sql(
            f"SELECT customer_id FROM {table}",
            engine
        )

        sql6_table = table
        sql6_ids = set(
            test_df["customer_id"]
        )

        break

    except Exception:
        continue


# ---------------------------------------------------------
# If SQL6 table exists
# ---------------------------------------------------------

if sql6_table:

    ml_ids = set(
        top_20["customer_id"]
    )

    overlap = ml_ids.intersection(
        sql6_ids
    )

    print(
        f"SQL6 table: {sql6_table}"
    )

    print(
        f"SQL6 high-risk customers: {len(sql6_ids)}"
    )

    print(
        f"ML top-20 customers: {len(ml_ids)}"
    )

    print(
        f"Overlap: {len(overlap)}"
    )

    if overlap:

        print("\nCustomers appearing in BOTH lists:")

        for customer_id in sorted(overlap):

            print(customer_id)

    else:

        print(
            "\nNo overlap found."
            " This is possible because ML and rule-based"
            " methods use different logic."
        )

else:

    print(
        "SQL6 high-risk customer table was not found."
    )

    print(
        "Compare the customer IDs from this ML top-20 "
        "list with the SQL6 high-risk list manually."
    )


# =========================================================
# 262. BUSINESS INTERPRETATION
# =========================================================

print("\n" + "=" * 60)
print("BUSINESS INTERPRETATION")
print("=" * 60)

print(
    "1. Customers most likely to churn are those whose "
    "profile contains the strongest positive churn drivers "
    "identified by the model."
)

print(
    "2. Customers with short-term or month-to-month "
    "contracts should receive particular attention because "
    "these customers generally have less commitment."
)

print(
    "3. Customers with higher-risk service and billing "
    "patterns should be prioritized for proactive retention "
    "offers."
)

print(
    "4. The retention team can use the ML risk score to "
    "prioritize customers instead of treating every "
    "customer as equally likely to churn."
)

print(
    "5. The highest-risk customers should be contacted "
    "early with targeted offers, contract incentives, or "
    "service support before they actually churn."
)


# =========================================================
# COMPLETE
# =========================================================

print("\n" + "=" * 60)
print("ML3 MODEL INTERPRETATION COMPLETE")
print("=" * 60)