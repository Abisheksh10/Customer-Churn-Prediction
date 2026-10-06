import joblib
import pandas as pd


# =========================================================
# LOAD MODEL ONCE
# =========================================================

MODEL_PATH = r"D:\tasks\phase6\models\tree_churn.pkl"

model = joblib.load(MODEL_PATH)

print("Churn model loaded successfully.")


# =========================================================
# MODEL FEATURES
# =========================================================

MODEL_FEATURES = list(model.feature_names_in_)

print("Model expects features:")
print(MODEL_FEATURES)


# =========================================================
# PREPROCESS INPUT
# =========================================================

def preprocess_input(
    tenure,
    monthly_charges,
    contract_type,
    service_count
):
    """
    Convert API input into the exact feature format
    expected by the trained ML model.
    """

    # -----------------------------------------------------
    # Create one-row DataFrame
    # -----------------------------------------------------

    data = {
        "tenure": [tenure],
        "monthly_charges": [monthly_charges],
        "service_count": [service_count],
        "contract": [contract_type]
    }

    df = pd.DataFrame(data)


    # -----------------------------------------------------
    # Engineered features
    # -----------------------------------------------------

    # Same threshold used in DE4/CP4
    # Replace this with the actual training median
    # if your ML2 feature pipeline used a different value.
    HIGH_CHARGE_THRESHOLD = 70.35

    df["high_charge_flag"] = (
        df["monthly_charges"] > HIGH_CHARGE_THRESHOLD
    ).astype(int)


    df["is_long_term_customer"] = (
        df["tenure"] >= 24
    ).astype(int)


    # We don't receive these values from the API,
    # so use defaults consistent with a simple prediction API.
    df["has_streaming_bundle"] = 0
    df["auto_pay_flag"] = 0


    # -----------------------------------------------------
    # Tenure bucket
    # -----------------------------------------------------

    def create_tenure_bucket(tenure):

        if tenure <= 12:
            return "0-12"

        elif tenure <= 24:
            return "12-24"

        elif tenure <= 48:
            return "24-48"

        else:
            return "48-72"


    df["tenure_bucket"] = df["tenure"].apply(
        create_tenure_bucket
    )


    # -----------------------------------------------------
    # Total charges
    # -----------------------------------------------------

    # API doesn't provide total_charges.
    # Approximate it from tenure × monthly charges.
    df["total_charges"] = (
        df["tenure"] *
        df["monthly_charges"]
    )


    # -----------------------------------------------------
    # Internet service
    # -----------------------------------------------------

    # API doesn't provide internet_service.
    # Use a default category.
    df["internet_service"] = "DSL"


    # -----------------------------------------------------
    # One-hot encoding
    # -----------------------------------------------------

    df = pd.get_dummies(
        df,
        columns=[
            "contract",
            "internet_service"
        ],
        drop_first=False
    )


    # -----------------------------------------------------
    # Ensure every model feature exists
    # -----------------------------------------------------

    for feature in MODEL_FEATURES:

        if feature not in df.columns:
            df[feature] = 0


    # -----------------------------------------------------
    # Remove features not used by model
    # -----------------------------------------------------

    df = df[MODEL_FEATURES]


    # -----------------------------------------------------
    # Convert to integer where appropriate
    # -----------------------------------------------------

    for column in df.columns:

        if df[column].dtype == bool:
            df[column] = df[column].astype(int)


    return df


# =========================================================
# PREDICT CHURN
# =========================================================

def predict_churn(
    tenure,
    monthly_charges,
    contract_type,
    service_count
):

    # -----------------------------------------------------
    # Prepare input
    # -----------------------------------------------------

    X = preprocess_input(
        tenure=tenure,
        monthly_charges=monthly_charges,
        contract_type=contract_type,
        service_count=service_count
    )


    # -----------------------------------------------------
    # Prediction
    # -----------------------------------------------------

    prediction = model.predict(X)[0]


    # -----------------------------------------------------
    # Churn probability
    # -----------------------------------------------------

    probability = model.predict_proba(X)[0][1]


    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    if prediction == 1:

        result = "Likely to churn"

    else:

        result = "Unlikely to churn"


    return {
        "risk_score": round(float(probability), 4),
        "prediction": result,
        "confidence": round(
            float(max(probability, 1 - probability)),
            4
        )
    }