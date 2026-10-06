import pandas as pd
from customer_cleaner import CustomerCleaner


df = pd.read_csv("telecom_churn.csv")


cleaner = CustomerCleaner(df)


clean_df = cleaner.clean()


print(clean_df.head())



contract_churn=(clean_df
                .groupby("contract")["churn"]
                .mean()
                .sort_values(ascending=False))

print(contract_churn)




internet_churn = (
    clean_df
    .groupby("internet_service")["churn"]
    .mean()
    .sort_values(ascending=False)
)


print(internet_churn)



payment_churn = (
    clean_df
    .groupby("payment_method")["churn"]
    .mean()
    .sort_values(ascending=False)
)


print(payment_churn)


clean_df["tenure_bucket"] = pd.cut(
    clean_df["tenure"],
    bins=[0,12,24,48,72],
    labels=[
        "0-12",
        "13-24",
        "25-48",
        "49-72"
    ],
    include_lowest=True
)






tenure_churn = (
    clean_df
    .groupby("tenure_bucket",
             observed=False)["churn"]
    .mean()
    .sort_values(ascending=False)
)


print(tenure_churn)




monthly_charge_analysis = (
    clean_df
    .groupby("churn")["monthly_charges"]
    .mean()
)


print(monthly_charge_analysis)



segment_churn = (
    clean_df
    .groupby(
        [
            "contract",
            "internet_service"
        ]
    )["churn"]
    .mean()
    .sort_values(
        ascending=False
    )
)


print(segment_churn)
















# Customers on month-to-month contracts have the highest churn risk, especially those using fiber optic internet services. Customers paying through electronic checks and newer customers with less than one year of tenure also show higher likelihood of leaving. The retention team should focus on converting high-risk customers to longer contracts, improving early customer engagement, and offering targeted incentives to reduce churn.














#cp4 
