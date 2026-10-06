import os
import joblib
import pandas as pd

from sqlalchemy import create_engine

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

engine = create_engine(
    "mysql+pymysql://root:root@localhost/telecom"
)


# =========================================================
# LOAD DATA
# =========================================================

print("Loading customer_ml_features...")

df = pd.read_sql(
    "SELECT * FROM customer_ml_features",
    engine
)

print(f"Rows loaded: {len(df)}")


# =========================================================
# DEFINE FEATURES
# =========================================================

target = "churn"

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

categorical_columns = [
    "contract",
    "internet_service"
]


# =========================================================
# CREATE X AND y
# =========================================================

X = df[
    numeric_columns + categorical_columns
].copy()

y = df[target].copy()


# =========================================================
# ONE-HOT ENCODING
# =========================================================

X = pd.get_dummies(
    X,
    columns=categorical_columns,
    drop_first=False,
    dtype=int
)


print("\nFEATURE MATRIX")
print("=" * 60)

print("X shape:", X.shape)
print("y shape:", y.shape)

print("\nFeatures:")
print(X.columns.tolist())


# =========================================================
# CLASS BALANCE
# =========================================================

print("\nCLASS BALANCE")
print("=" * 60)

print(y.value_counts())

print("\nClass proportions:")

print(
    y.value_counts(normalize=True)
)


# =========================================================
# TRAIN / TEST SPLIT
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42
)


print("\nTRAIN / TEST SPLIT")
print("=" * 60)

print("Training rows:", len(X_train))
print("Testing rows :", len(X_test))


# =========================================================
# CREATE MODELS
# =========================================================

logistic_model = LogisticRegression(
    max_iter=1000
)

tree_model = DecisionTreeClassifier(
    max_depth=5,
    random_state=42
)


# =========================================================
# TRAIN LOGISTIC REGRESSION
# =========================================================

print("\nTraining Logistic Regression...")

logistic_model.fit(
    X_train,
    y_train
)

print("Logistic Regression training complete.")


# =========================================================
# TRAIN DECISION TREE
# =========================================================

print("\nTraining Decision Tree...")

tree_model.fit(
    X_train,
    y_train
)

print("Decision Tree training complete.")


# =========================================================
# PREDICTIONS
# =========================================================

logistic_predictions = logistic_model.predict(X_test)

tree_predictions = tree_model.predict(X_test)


# =========================================================
# LOGISTIC REGRESSION REPORT
# =========================================================

print("\n")
print("=" * 70)
print("LOGISTIC REGRESSION")
print("=" * 70)

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        logistic_predictions,
        target_names=["Active", "Churned"]
    )
)


print("Confusion Matrix:")

print(
    confusion_matrix(
        y_test,
        logistic_predictions
    )
)


# =========================================================
# DECISION TREE REPORT
# =========================================================

print("\n")
print("=" * 70)
print("DECISION TREE")
print("=" * 70)

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        tree_predictions,
        target_names=["Active", "Churned"]
    )
)


print("Confusion Matrix:")

print(
    confusion_matrix(
        y_test,
        tree_predictions
    )
)


# =========================================================
# 5-FOLD CROSS VALIDATION
# =========================================================

print("\n")
print("=" * 70)
print("5-FOLD CROSS VALIDATION")
print("=" * 70)


logistic_cv_scores = cross_val_score(
    logistic_model,
    X,
    y,
    cv=5,
    scoring="f1"
)

tree_cv_scores = cross_val_score(
    tree_model,
    X,
    y,
    cv=5,
    scoring="f1"
)


print("\nLogistic Regression CV F1 scores:")

print(logistic_cv_scores)

print(
    "Logistic Regression Mean CV F1:",
    logistic_cv_scores.mean()
)


print("\nDecision Tree CV F1 scores:")

print(tree_cv_scores)

print(
    "Decision Tree Mean CV F1:",
    tree_cv_scores.mean()
)


# =========================================================
# CALCULATE TEST METRICS
# =========================================================

logistic_accuracy = accuracy_score(
    y_test,
    logistic_predictions
)

logistic_precision = precision_score(
    y_test,
    logistic_predictions,
    pos_label=1
)

logistic_recall = recall_score(
    y_test,
    logistic_predictions,
    pos_label=1
)

logistic_f1 = f1_score(
    y_test,
    logistic_predictions,
    pos_label=1
)


tree_accuracy = accuracy_score(
    y_test,
    tree_predictions
)

tree_precision = precision_score(
    y_test,
    tree_predictions,
    pos_label=1
)

tree_recall = recall_score(
    y_test,
    tree_predictions,
    pos_label=1
)

tree_f1 = f1_score(
    y_test,
    tree_predictions,
    pos_label=1
)


# =========================================================
# COMPARISON TABLE
# =========================================================

comparison = pd.DataFrame({

    "Model": [
        "Logistic Regression",
        "Decision Tree"
    ],

    "Accuracy": [
        logistic_accuracy,
        tree_accuracy
    ],

    "Precision (Churned)": [
        logistic_precision,
        tree_precision
    ],

    "Recall (Churned)": [
        logistic_recall,
        tree_recall
    ],

    "F1 (Churned)": [
        logistic_f1,
        tree_f1
    ],

    "CV F1": [
        logistic_cv_scores.mean(),
        tree_cv_scores.mean()
    ]
})


print("\n")
print("=" * 90)
print("MODEL COMPARISON")
print("=" * 90)

print(
    comparison.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# =========================================================
# SELECT BETTER MODEL
# =========================================================

if logistic_f1 > tree_f1:

    best_model_name = "Logistic Regression"
    best_model = logistic_model

else:

    best_model_name = "Decision Tree"
    best_model = tree_model


print("\n")
print("=" * 70)
print("MODEL SELECTION")
print("=" * 70)

print(
    f"Better model based on Churned F1: {best_model_name}"
)


# =========================================================
# SAVE MODELS
# =========================================================

os.makedirs(
    "models",
    exist_ok=True
)


joblib.dump(
    logistic_model,
    "models/logistic_churn.pkl"
)

joblib.dump(
    tree_model,
    "models/tree_churn.pkl"
)


print("\nModels saved:")

print("models/logistic_churn.pkl")
print("models/tree_churn.pkl")


# =========================================================
# FINAL SUMMARY
# =========================================================

print("\n")
print("=" * 70)
print("ML2 MODEL TRAINING COMPLETE")
print("=" * 70)

print(f"Best model: {best_model_name}")

print(
    f"Logistic Regression Churn F1: "
    f"{logistic_f1:.4f}"
)

print(
    f"Decision Tree Churn F1: "
    f"{tree_f1:.4f}"
)

print(
    f"Logistic Regression CV F1: "
    f"{logistic_cv_scores.mean():.4f}"
)

print(
    f"Decision Tree CV F1: "
    f"{tree_cv_scores.mean():.4f}"
)