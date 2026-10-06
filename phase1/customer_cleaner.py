#task 2

import pandas as pd
import logging


logging.basicConfig(level=logging.INFO,format="%(levelname)s: %(message)s")


class CustomerCleaner:


    def __init__(self, df):

        self.df = df.copy()

        logging.info(
            "CustomerCleaner initialized"
        )


    def standardize_column_names(self):

        logging.info(
            "Standardizing column names"
        )

        self.df.columns = (
            self.df.columns
            .str.replace(
                r'([a-z])([A-Z])',
                r'\1_\2',
                regex=True
            )
            .str.lower()
        )

        return self.df


    def fix_total_charges(self):

        logging.info(
            "Fixing total_charges"
        )

        try:

            affected_rows = (
                self.df["total_charges"]
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )

            self.df["total_charges"] = (
                self.df["total_charges"]
                .replace("", pd.NA)
            )

            self.df["total_charges"] = pd.to_numeric(
                self.df["total_charges"],
                errors="coerce"
            ).astype(float)

            logging.info(
                f"Affected rows: {affected_rows}"
            )

        except Exception as e:

            logging.error(
                f"Error fixing total_charges: {e}"
            )

        return self.df


    def normalize_binary_columns(self):

        logging.info(
            "Normalizing binary columns"
        )

        columns = [
            "partner",
            "dependents",
            "phone_service",
            "paperless_billing",
            "churn"
        ]

        mapping = {
            "Yes": 1,
            "No": 0
        }

        for col in columns:
            self.df[col] = self.df[col].map(mapping)

        return self.df


    def handle_nulls(self):

        logging.info(
            "Handling null values"
        )

        missing = self.df["total_charges"].isna().sum()

        self.df["total_charges"] = (
            self.df["total_charges"]
            .fillna(
                self.df["monthly_charges"]
            )
        )

        logging.info(
            f"Filled {missing} null total_charges values"
        )

        return self.df


    def clean(self):

        logging.info(
            "Running full cleaning process"
        )

        self.standardize_column_names()
        self.fix_total_charges()
        self.normalize_binary_columns()
        self.handle_nulls()

        logging.info(
            "Cleaning completed"
        )

        return self.df