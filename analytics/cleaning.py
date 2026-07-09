"""
cleaning.py
------------
Cleans the raw RetailIQ sales dataset and exports an analysis-ready CSV.

Run:
    python analytics/cleaning.py

Input : data/raw/retail_sales_raw.csv
Output: data/cleaned/retail_sales_cleaned.csv

Steps performed (in order):
    1. Load raw data
    2. Fix data types (Quantity, Date, Discount)
    3. Handle invalid / unparsable dates
    4. Remove duplicate rows
    5. Handle missing values
    6. Fix negative quantities (data entry sign errors)
    7. Detect & cap outliers in Sales (IQR method)
    8. Feature engineering (Year, Month, Quarter, Weekday, Net_Sales, Margin_%)
    9. Save cleaned dataset + a short data-quality report
"""

import pandas as pd
import numpy as np
import re
import os

RAW_PATH = "data/raw/retail_sales_raw.csv"
CLEANED_PATH = "data/cleaned/retail_sales_cleaned.csv"
REPORT_PATH = "reports/data_quality_report.txt"


def log(msg, report_lines):
    print(msg)
    report_lines.append(msg)


def clean_quantity(value):
    """Extract an integer quantity from values like '2 units' or -3."""
    if pd.isna(value):
        return np.nan
    if isinstance(value, str):
        match = re.search(r"-?\d+", value)
        if match:
            return int(match.group())
        return np.nan
    return int(value)


def parse_date(value):
    """Try multiple date formats; return NaT if unparsable."""
    try:
        return pd.to_datetime(value, format="%Y-%m-%d")
    except (ValueError, TypeError):
        return pd.NaT


def main():
    report = []
    os.makedirs("data/cleaned", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    df = pd.read_csv(RAW_PATH)
    log(f"Loaded raw data: {df.shape[0]} rows, {df.shape[1]} columns", report)

    # ---- 1. Fix Quantity dtype -------------------------------------------------
    df["Quantity"] = df["Quantity"].apply(clean_quantity)

    # ---- 2. Fix negative quantities (assume sign-entry error -> take abs) ------
    neg_count = (df["Quantity"] < 0).sum()
    df["Quantity"] = df["Quantity"].abs()
    log(f"Fixed {neg_count} negative Quantity values (converted to absolute value)", report)

    # ---- 3. Parse dates ---------------------------------------------------------
    df["Date_parsed"] = df["Date"].apply(parse_date)
    bad_dates = df["Date_parsed"].isna().sum()
    log(f"Found {bad_dates} invalid/unparsable dates -> rows dropped", report)
    df = df[df["Date_parsed"].notna()].copy()
    df["Date"] = df["Date_parsed"]
    df.drop(columns=["Date_parsed"], inplace=True)

    # ---- 4. Remove duplicates ----------------------------------------------------
    before = len(df)
    df = df.drop_duplicates()
    log(f"Removed {before - len(df)} exact duplicate rows", report)

    # ---- 5. Handle missing values -------------------------------------------------
    missing_before = df.isna().sum()
    log("Missing values before imputation:\n" + missing_before[missing_before > 0].to_string(), report)

    df["Customer_Name"] = df["Customer_Name"].fillna("Unknown Customer")
    df["City"] = df["City"].fillna(df.groupby("State")["City"].transform(
        lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown"))
    df["City"] = df["City"].fillna("Unknown")
    df["Discount"] = df["Discount"].fillna(0.0)
    df["Payment_Method"] = df["Payment_Method"].fillna("Unknown")
    df["Quantity"] = df["Quantity"].fillna(df["Quantity"].median())

    missing_after = df.isna().sum().sum()
    log(f"Total remaining missing values after imputation: {missing_after}", report)

    # ---- 6. Recalculate Sales / Cost / Profit for consistency ---------------------
    # After cleaning Quantity, recompute Sales using Unit_Price & Discount so
    # figures stay internally consistent (guards against the injected outliers too).
    df["Sales_recalculated"] = (df["Quantity"] * df["Unit_Price"] * (1 - df["Discount"])).round(2)

    # ---- 7. Outlier detection & capping (IQR method, PER CATEGORY) ----------------
    # Sales ranges differ hugely across categories (e.g. Electronics vs Grocery),
    # so a single global IQR would wrongly flag genuine high-value electronics
    # orders as outliers. Applying IQR within each Category is more realistic.
    def cap_outliers_per_group(group):
        q1, q3 = group.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower = max(0, q1 - 1.5 * iqr)
        upper = q3 + 1.5 * iqr
        return group.clip(lower=lower, upper=upper)

    outliers_before = df["Sales_recalculated"].copy()
    df["Sales"] = df.groupby("Category")["Sales_recalculated"].transform(cap_outliers_per_group)
    outliers = (df["Sales"] != outliers_before).sum()
    log(f"Capped {outliers} outliers in Sales via per-category IQR method", report)
    df.drop(columns=["Sales_recalculated"], inplace=True)

    df["Cost"] = (df["Quantity"] * df["Unit_Price"] * 0.68).round(2)  # avg cost ratio fallback
    df["Profit"] = (df["Sales"] - df["Cost"]).round(2)

    # ---- 8. Feature engineering -----------------------------------------------------
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Month_Name"] = df["Date"].dt.strftime("%b")
    df["Quarter"] = df["Date"].dt.quarter
    df["Weekday"] = df["Date"].dt.day_name()
    df["Is_Weekend"] = df["Weekday"].isin(["Saturday", "Sunday"])
    df["Net_Sales"] = df["Sales"]
    df["Margin_Pct"] = np.where(df["Sales"] > 0, (df["Profit"] / df["Sales"] * 100).round(2), 0)

    # ---- 9. Final column ordering & save --------------------------------------------
    ordered_cols = [
        "Order_ID", "Date", "Year", "Month", "Month_Name", "Quarter", "Weekday", "Is_Weekend",
        "Customer_ID", "Customer_Name", "City", "State", "Region",
        "Store_ID", "Store_Name",
        "Product_ID", "Product_Name", "Category", "Sub_Category",
        "Quantity", "Unit_Price", "Discount", "Sales", "Cost", "Profit", "Margin_Pct",
        "Supplier", "Payment_Method",
    ]
    df = df[ordered_cols]

    df.to_csv(CLEANED_PATH, index=False)
    log(f"\nSaved cleaned dataset: {CLEANED_PATH} -> {df.shape[0]} rows, {df.shape[1]} columns", report)

    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(str(x) for x in report))
    print(f"\nData quality report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
