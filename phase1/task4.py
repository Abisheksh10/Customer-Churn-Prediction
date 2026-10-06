import pandas as pd
from customer_cleaner import CustomerCleaner


# Load data
df = pd.read_csv("telecom_churn.csv")


# Clean data
cleaner = CustomerCleaner(df)

clean_df = cleaner.clean()


# Feature 1
clean_df["tenure_bucket"] = pd.cut(
    clean_df["tenure"],
    bins=[0,12,24,48,72],
    labels=[
        "0-12",
        "13-24",
        "25-48",
        "49-72"
    ]
)


# Feature 2
median_charge = clean_df["monthly_charges"].median()

clean_df["high_charge_flag"] = (
    clean_df["monthly_charges"] > median_charge
).astype(int)


# Feature 3
service_columns = [
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies"
]
clean_df[service_columns] = (
    clean_df[service_columns]
    .replace({
        "Yes": 1,
        "No": 0,
        "No internet service": 0
    })
)
clean_df["service_count"] = (
    clean_df[service_columns]
    .sum(axis=1)
)


# Feature 4
clean_df["is_long_term_customer"] = (
    clean_df["tenure"] >= 24
).astype(int)


# Feature 5
clean_df["has_streaming_bundle"] = (
    (
        clean_df["streaming_tv"] == 1
    )
    &
    (
        clean_df["streaming_movies"] == 1
    )
).astype(int)


# Feature 6
clean_df["auto_pay_flag"] = (
    clean_df["payment_method"]
    .str.contains(
        "automatic",
        case=False,
        na=False
    )
).astype(int)




# Correlation
features = [
    "high_charge_flag",
    "service_count",
    "is_long_term_customer",
    "has_streaming_bundle",
    "auto_pay_flag"
]

print(clean_df[features].dtypes)
print(clean_df["churn"].dtype)
print(clean_df["churn"].unique())



print(
    clean_df[features]
    .corrwith(clean_df["churn"])
)


# Save ML dataset
clean_df.to_csv(
    "customer_features.csv",
    index=False
)



