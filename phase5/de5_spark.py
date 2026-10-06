from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType
)
import pandas as pd
import os
import shutil


# --------------------------------------------------
# 202. Create SparkSession
# --------------------------------------------------

spark = (
    SparkSession.builder
    .appName("DE5 Churn Analysis")
    .master("local[2]")
    .config("spark.driver.memory", "4g")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# --------------------------------------------------
# 203. Define manual schema
# --------------------------------------------------

schema = StructType([

    StructField("customerID", StringType(), True),
    StructField("gender", StringType(), True),
    StructField("SeniorCitizen", IntegerType(), True),
    StructField("Partner", StringType(), True),
    StructField("Dependents", StringType(), True),
    StructField("tenure", IntegerType(), True),
    StructField("PhoneService", StringType(), True),
    StructField("MultipleLines", StringType(), True),
    StructField("InternetService", StringType(), True),
    StructField("OnlineSecurity", StringType(), True),
    StructField("OnlineBackup", StringType(), True),
    StructField("DeviceProtection", StringType(), True),
    StructField("TechSupport", StringType(), True),
    StructField("StreamingTV", StringType(), True),
    StructField("StreamingMovies", StringType(), True),
    StructField("Contract", StringType(), True),
    StructField("PaperlessBilling", StringType(), True),
    StructField("PaymentMethod", StringType(), True),
    StructField("MonthlyCharges", DoubleType(), True),
    StructField("TotalCharges", StringType(), True),
    StructField("Churn", StringType(), True)

])


# --------------------------------------------------
# 204. Read CSV
# --------------------------------------------------

csv_path = "telecom_churn.csv"

df = (
    spark.read
    .option("header", True)
    .schema(schema)
    .csv(csv_path)
)

print("\n===== SPARK SCHEMA BEFORE CLEANING =====")
df.printSchema()

print("\n===== ROW COUNT =====")
print(df.count())


# --------------------------------------------------
# 205. Fix TotalCharges blanks
# --------------------------------------------------

df = df.withColumn(
    "TotalCharges",
    F.regexp_replace(
        F.trim(F.col("TotalCharges")),
        "^$",#matches an empty string.
        None
    ).cast(DoubleType())
)


# --------------------------------------------------
# 206. Encode Churn
# --------------------------------------------------

df = df.withColumn(
    "churn_encoded",
    F.when(
        F.col("Churn") == "Yes",
        1
    ).otherwise(0)
)


print("\n===== SCHEMA AFTER CLEANING =====")
df.printSchema()


# --------------------------------------------------
# 207. GroupBy Contract
# --------------------------------------------------

contract_summary = (
    df.groupBy("Contract")
    .agg(
        F.count("*").alias("customer_count"),
        F.avg("churn_encoded").alias("churn_rate")
    )
    .orderBy(
        F.col("churn_rate").desc()
    )
)

print("\n===== CHURN RATE BY CONTRACT =====")

contract_summary.show(
    truncate=False
)


# --------------------------------------------------
# 208. GroupBy InternetService
# --------------------------------------------------

internet_summary = (
    df.groupBy("InternetService")
    .agg(
        F.avg("MonthlyCharges").alias(
            "avg_monthly_charges"
        ),
        F.avg("churn_encoded").alias(
            "churn_rate"
        )
    )
    .orderBy(
        F.col("churn_rate").desc()
    )
)


print("\n===== INTERNET SERVICE SUMMARY =====")

internet_summary.show(
    truncate=False
)


# --------------------------------------------------
# 209. Cross-validation
# --------------------------------------------------

print("\n===== CONTRACT CHURN RATES FOR CROSS-VALIDATION =====")

contract_summary.select(
    "Contract",
    "churn_rate"
).show(
    truncate=False
)


# --------------------------------------------------
# 210. Write contract summary as Parquet
# --------------------------------------------------

print("\n===== WRITING PARQUET =====")

output_path = "data/spark_output/contract_summary"

# Remove previous output if it exists
if os.path.exists(output_path):
    shutil.rmtree(output_path)

# Convert only the small aggregated Spark DataFrame to pandas
contract_summary_pd = contract_summary.toPandas()

# Write partitioned Parquet using pandas + PyArrow
contract_summary_pd.to_parquet(
    output_path,
    engine="pyarrow",
    partition_cols=["Contract"],
    index=False
)

print(f"Parquet written to: {output_path}")


# --------------------------------------------------
# 211. Read Parquet back
# --------------------------------------------------

print("\n===== PARQUET ROUND-TRIP =====")

parquet_df = pd.read_parquet(
    output_path,
    engine="pyarrow"
)

print("\nParquet schema:")
print(parquet_df.dtypes)

print("\nParquet row count:")
print(len(parquet_df))

print("\nParquet data:")
print(parquet_df)

# --------------------------------------------------
# Stop Spark
# --------------------------------------------------

spark.stop()

print("\nDE5 Spark pipeline completed successfully.")