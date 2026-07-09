"""
analysis.py
------------
Exploratory Data Analysis (EDA) for the cleaned RetailIQ dataset.
Generates all charts referenced in the README / interview prep as PNGs
in reports/screenshots/, and prints key numeric insights to the console.

Run:
    python analytics/analysis.py
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import seaborn as sns
import os

sns.set_theme(style="whitegrid")
OUT_DIR = "reports/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv("data/cleaned/retail_sales_cleaned.csv", parse_dates=["Date"])

print("=" * 70)
print("RETAILIQ - EXPLORATORY DATA ANALYSIS")
print("=" * 70)
print(f"Rows: {len(df):,}  | Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
print(f"Total Revenue: Rs.{df['Sales'].sum():,.0f}")
print(f"Total Profit : Rs.{df['Profit'].sum():,.0f}")
print(f"Total Orders : {df['Order_ID'].nunique():,}")


def savefig(name):
    path = os.path.join(OUT_DIR, name)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"Saved chart: {path}")


# 1. Monthly sales trend ------------------------------------------------------
monthly = df.groupby(df["Date"].dt.to_period("M"))["Sales"].sum()
plt.figure(figsize=(12, 5))
monthly.plot(kind="line", marker="o", color="#2563eb")
plt.title("Monthly Sales Trend")
plt.xlabel("Month")
plt.ylabel("Revenue (Rs.)")
savefig("01_monthly_sales_trend.png")

# 2. Revenue by category -------------------------------------------------------
cat_rev = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
plt.figure(figsize=(10, 5))
sns.barplot(x=cat_rev.values, y=cat_rev.index, palette="viridis")
plt.title("Revenue by Category")
plt.xlabel("Revenue (Rs.)")
savefig("02_revenue_by_category.png")

# 3. Revenue by region ----------------------------------------------------------
region_rev = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
plt.figure(figsize=(8, 5))
sns.barplot(x=region_rev.index, y=region_rev.values, palette="mako")
plt.title("Revenue by Region")
plt.ylabel("Revenue (Rs.)")
savefig("03_revenue_by_region.png")

# 4. Top 10 products ------------------------------------------------------------
top_products = df.groupby("Product_Name")["Sales"].sum().sort_values(ascending=False).head(10)
plt.figure(figsize=(10, 6))
sns.barplot(x=top_products.values, y=top_products.index, palette="crest")
plt.title("Top 10 Products by Revenue")
plt.xlabel("Revenue (Rs.)")
savefig("04_top_10_products.png")

# 5. Worst 10 products ------------------------------------------------------------
worst_products = df.groupby("Product_Name")["Sales"].sum().sort_values(ascending=True).head(10)
plt.figure(figsize=(10, 6))
sns.barplot(x=worst_products.values, y=worst_products.index, palette="rocket")
plt.title("Bottom 10 Products by Revenue")
plt.xlabel("Revenue (Rs.)")
savefig("05_worst_10_products.png")

# 6. Store comparison ------------------------------------------------------------
store_rev = df.groupby("Store_Name")["Sales"].sum().sort_values(ascending=False)
plt.figure(figsize=(10, 6))
sns.barplot(x=store_rev.values, y=store_rev.index, palette="flare")
plt.title("Revenue by Store")
plt.xlabel("Revenue (Rs.)")
savefig("06_store_comparison.png")

# 7. Customer segmentation (spend distribution) ------------------------------------
cust_spend = df.groupby("Customer_ID")["Sales"].sum()
plt.figure(figsize=(9, 5))
sns.histplot(cust_spend, bins=50, color="#7c3aed", kde=True)
plt.title("Customer Spend Distribution")
plt.xlabel("Total Spend (Rs.)")
savefig("07_customer_spend_distribution.png")

# 8. Profit distribution -------------------------------------------------------------
plt.figure(figsize=(9, 5))
sns.histplot(df["Profit"], bins=60, color="#059669", kde=True)
plt.title("Profit Distribution (per line item)")
plt.xlabel("Profit (Rs.)")
savefig("08_profit_distribution.png")

# 9. Discount impact on margin -----------------------------------------------------
df["Discount_Band"] = pd.cut(df["Discount"], bins=[-0.01, 0, 0.1, 0.2, 1],
                              labels=["No Discount", "1-10%", "11-20%", "20%+"])
discount_margin = df.groupby("Discount_Band", observed=True)["Margin_Pct"].mean()
plt.figure(figsize=(8, 5))
sns.barplot(x=discount_margin.index, y=discount_margin.values, palette="coolwarm")
plt.title("Average Margin % by Discount Band")
plt.ylabel("Average Margin %")
savefig("09_discount_impact_on_margin.png")

# 10. Correlation heatmap -------------------------------------------------------------
numeric_cols = ["Quantity", "Unit_Price", "Discount", "Sales", "Cost", "Profit", "Margin_Pct"]
plt.figure(figsize=(9, 7))
sns.heatmap(df[numeric_cols].corr(), annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation Heatmap")
savefig("10_correlation_heatmap.png")

# 11. Seasonality - avg sales by month name across years -------------------------------
month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
seasonal = df.groupby("Month_Name")["Sales"].sum().reindex(month_order)
plt.figure(figsize=(11, 5))
sns.barplot(x=seasonal.index, y=seasonal.values, palette="cubehelix")
plt.title("Seasonality: Total Revenue by Calendar Month")
plt.ylabel("Revenue (Rs.)")
savefig("11_seasonality_by_month.png")

# 12. Weekday vs weekend --------------------------------------------------------------
weekday_rev = df.groupby("Is_Weekend")["Sales"].sum()
weekday_rev.index = ["Weekday", "Weekend"]
plt.figure(figsize=(6, 5))
sns.barplot(x=weekday_rev.index, y=weekday_rev.values, palette="pastel")
plt.title("Weekday vs Weekend Revenue")
savefig("12_weekday_vs_weekend.png")

print("\nEDA complete. All charts saved to reports/screenshots/")
