"""
generate_dataset.py
--------------------
Generates a realistic SYNTHETIC retail sales dataset for the RetailIQ project.

Why synthetic data?
A real company dataset isn't publicly available for this exact schema, so we
generate a statistically realistic one instead. This is a very common and
accepted practice for fresher/portfolio projects - just be upfront about it
in interviews.

Output: data/raw/retail_sales_raw.csv  (~60,000 rows, deliberately "dirty")

The dataset is generated WITH intentional data quality issues (missing values,
duplicates, negative quantities, bad dates, outliers) so that the cleaning
script (cleaning.py) has real work to do - this is what makes the project
believable as a fresher's end-to-end pipeline instead of a toy example.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# Reproducibility
np.random.seed(42)
random.seed(42)

N_ROWS = 60000

# ----------------------------------------------------------------------
# 1. Reference / lookup data
# ----------------------------------------------------------------------

REGIONS_STATES_CITIES = {
    "North": {
        "Delhi": ["New Delhi", "Dwarka", "Rohini"],
        "Punjab": ["Ludhiana", "Amritsar"],
        "Uttar Pradesh": ["Lucknow", "Noida", "Kanpur"],
    },
    "South": {
        "Karnataka": ["Bengaluru", "Mysuru"],
        "Tamil Nadu": ["Chennai", "Coimbatore"],
        "Telangana": ["Hyderabad", "Warangal"],
    },
    "West": {
        "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
        "Gujarat": ["Ahmedabad", "Surat"],
        "Rajasthan": ["Jaipur", "Udaipur"],
    },
    "East": {
        "West Bengal": ["Kolkata", "Howrah"],
        "Odisha": ["Bhubaneswar"],
        "Bihar": ["Patna"],
    },
}

STORES = [
    ("ST001", "RetailIQ Delhi Central", "North"),
    ("ST002", "RetailIQ Noida Hub", "North"),
    ("ST003", "RetailIQ Bengaluru Tech Park", "South"),
    ("ST004", "RetailIQ Chennai Marina", "South"),
    ("ST005", "RetailIQ Mumbai Andheri", "West"),
    ("ST006", "RetailIQ Pune Camp", "West"),
    ("ST007", "RetailIQ Kolkata Park St", "East"),
    ("ST008", "RetailIQ Jaipur Malviya Nagar", "West"),
    ("ST009", "RetailIQ Hyderabad Hitech City", "South"),
    ("ST010", "RetailIQ Patna Boring Road", "East"),
]

CATEGORIES = {
    "Electronics": {
        "sub": ["Mobiles", "Laptops", "Headphones", "Smartwatches", "Cameras"],
        "price_range": (999, 85000),
        "supplier": ["TechDistro Pvt Ltd", "Global Electronics Supply Co"],
    },
    "Fashion": {
        "sub": ["Men's Clothing", "Women's Clothing", "Footwear", "Accessories"],
        "price_range": (299, 5000),
        "supplier": ["Trendy Textiles Ltd", "FabricWorld Wholesalers"],
    },
    "Home & Kitchen": {
        "sub": ["Cookware", "Furniture", "Home Decor", "Storage"],
        "price_range": (199, 25000),
        "supplier": ["HomeEssentials Pvt Ltd", "KitchenCraft Suppliers"],
    },
    "Grocery": {
        "sub": ["Staples", "Beverages", "Snacks", "Personal Care"],
        "price_range": (20, 1200),
        "supplier": ["DailyNeeds Distributors", "FreshMart Supply Chain"],
    },
    "Sports & Fitness": {
        "sub": ["Gym Equipment", "Outdoor Sports", "Yoga & Wellness"],
        "price_range": (149, 15000),
        "supplier": ["FitGear Traders", "SportsPoint Wholesale"],
    },
    "Books & Stationery": {
        "sub": ["Fiction", "Academic", "Office Supplies"],
        "price_range": (49, 2500),
        "supplier": ["PageTurner Distributors", "OfficeMart Supplies"],
    },
}

PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery"]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh",
               "Ananya", "Diya", "Isha", "Priya", "Kavya", "Riya", "Neha", "Pooja",
               "Rahul", "Rohan", "Karan", "Amit", "Suresh", "Anjali", "Sneha",
               "Meera", "Nikita", "Aryan", "Ishaan", "Kabir", "Tanya", "Simran", "Aditi"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Reddy", "Iyer", "Nair", "Patel", "Singh",
              "Kumar", "Das", "Mehta", "Joshi", "Rao", "Chatterjee", "Malhotra",
              "Kapoor", "Bansal", "Agarwal", "Pillai", "Menon"]

N_CUSTOMERS = 4000
customer_pool = []
for i in range(1, N_CUSTOMERS + 1):
    cust_id = f"CUST{i:05d}"
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    region = random.choice(list(REGIONS_STATES_CITIES.keys()))
    state = random.choice(list(REGIONS_STATES_CITIES[region].keys()))
    city = random.choice(REGIONS_STATES_CITIES[region][state])
    customer_pool.append((cust_id, name, city, state, region))

# Products catalogue (fixed, reused across many orders - realistic!)
N_PRODUCTS = 500
product_pool = []
pid = 1
for category, meta in CATEGORIES.items():
    n_products_in_cat = N_PRODUCTS // len(CATEGORIES)
    for _ in range(n_products_in_cat):
        sub_cat = random.choice(meta["sub"])
        low, high = meta["price_range"]
        price = round(np.random.uniform(low, high), 2)
        cost = round(price * np.random.uniform(0.55, 0.8), 2)  # cost is 55-80% of price
        supplier = random.choice(meta["supplier"])
        product_name = f"{sub_cat.split()[0]} {category.split()[0]} Model-{pid}"
        product_pool.append({
            "product_id": f"PRD{pid:05d}",
            "product_name": product_name,
            "category": category,
            "sub_category": sub_cat,
            "unit_price": price,
            "unit_cost": cost,
            "supplier": supplier,
            "initial_inventory": np.random.randint(20, 1000),
        })
        pid += 1

products_df = pd.DataFrame(product_pool)

# ----------------------------------------------------------------------
# 2. Generate transactions
# ----------------------------------------------------------------------

start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)
date_range_days = (end_date - start_date).days

rows = []
for i in range(1, N_ROWS + 1):
    order_id = f"ORD{i:06d}"

    # seasonality: bias more orders towards Oct-Jan (festive/holiday season)
    day_offset = np.random.randint(0, date_range_days)
    order_date = start_date + timedelta(days=day_offset)
    # add a seasonal boost by resampling some dates into Oct-Dec
    if np.random.rand() < 0.25:
        boosted_year = random.choice([2023, 2024, 2025])
        boosted_month = random.choice([10, 11, 12])
        boosted_day = np.random.randint(1, 28)
        order_date = datetime(boosted_year, boosted_month, boosted_day)

    customer = random.choice(customer_pool)
    cust_id, cust_name, city, state, region = customer

    store = random.choice(STORES)
    store_id, store_name, store_region = store

    product = product_pool[np.random.randint(0, len(product_pool))]

    quantity = np.random.choice([1, 1, 1, 2, 2, 3, 4, 5], p=[0.35, 0.2, 0.15, 0.12, 0.08, 0.05, 0.03, 0.02])
    unit_price = product["unit_price"]
    discount_pct = np.random.choice([0, 0, 0.05, 0.1, 0.15, 0.2, 0.3],
                                     p=[0.4, 0.15, 0.15, 0.12, 0.1, 0.05, 0.03])
    sales_amount = round(quantity * unit_price * (1 - discount_pct), 2)
    cost_amount = round(quantity * product["unit_cost"], 2)
    profit = round(sales_amount - cost_amount, 2)

    payment_method = random.choice(PAYMENT_METHODS)

    rows.append({
        "Order_ID": order_id,
        "Date": order_date.strftime("%Y-%m-%d"),
        "Customer_ID": cust_id,
        "Customer_Name": cust_name,
        "City": city,
        "State": state,
        "Region": region,
        "Store_ID": store_id,
        "Store_Name": store_name,
        "Product_ID": product["product_id"],
        "Product_Name": product["product_name"],
        "Category": product["category"],
        "Sub_Category": product["sub_category"],
        "Quantity": quantity,
        "Unit_Price": unit_price,
        "Discount": discount_pct,
        "Sales": sales_amount,
        "Cost": cost_amount,
        "Profit": profit,
        "Supplier": product["supplier"],
        "Payment_Method": payment_method,
    })

df = pd.DataFrame(rows)

# ----------------------------------------------------------------------
# 3. Inject realistic "dirtiness" so cleaning.py has real work to do
# ----------------------------------------------------------------------

n = len(df)

# 3a. Missing values (~2% of Customer_Name, ~1.5% of Discount, ~1% of City)
for col, frac in [("Customer_Name", 0.02), ("Discount", 0.015), ("City", 0.01), ("Payment_Method", 0.01)]:
    idx = np.random.choice(n, size=int(n * frac), replace=False)
    df.loc[idx, col] = np.nan

# 3b. Duplicate rows (~1.5%)
dup_idx = np.random.choice(n, size=int(n * 0.015), replace=False)
df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)

# 3c. Negative quantity / sales typos (~0.5%)
neg_idx = np.random.choice(len(df), size=int(len(df) * 0.005), replace=False)
df.loc[neg_idx, "Quantity"] = -df.loc[neg_idx, "Quantity"]

# 3d. Invalid / malformed dates (~0.5%)
bad_date_idx = np.random.choice(len(df), size=int(len(df) * 0.005), replace=False)
bad_dates = ["31/02/2023", "2024-13-01", "0000-00-00", "not_a_date", "2025-02-30"]
df.loc[bad_date_idx, "Date"] = np.random.choice(bad_dates, size=len(bad_date_idx))

# 3e. Wrong data types - store Quantity as string for a slice of rows
df["Quantity"] = df["Quantity"].astype(object)
str_qty_idx = np.random.choice(len(df), size=int(len(df) * 0.01), replace=False)
df.loc[str_qty_idx, "Quantity"] = df.loc[str_qty_idx, "Quantity"].astype(str) + " units"

# 3f. Outliers in Sales (data entry errors, e.g. extra zero)
outlier_idx = np.random.choice(len(df), size=int(len(df) * 0.003), replace=False)
df.loc[outlier_idx, "Sales"] = df.loc[outlier_idx, "Sales"] * 100

# Shuffle rows so duplicates/errors aren't clustered at the end
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# ----------------------------------------------------------------------
# 4. Save raw dataset + supporting reference tables
# ----------------------------------------------------------------------

df.to_csv("/home/claude/RetailIQ/data/raw/retail_sales_raw.csv", index=False)
products_df.to_csv("/home/claude/RetailIQ/data/raw/products_reference.csv", index=False)

customers_df = pd.DataFrame(customer_pool, columns=["Customer_ID", "Customer_Name", "City", "State", "Region"])
customers_df.to_csv("/home/claude/RetailIQ/data/raw/customers_reference.csv", index=False)

stores_df = pd.DataFrame(STORES, columns=["Store_ID", "Store_Name", "Region"])
stores_df.to_csv("/home/claude/RetailIQ/data/raw/stores_reference.csv", index=False)

print(f"Raw transactional rows generated: {len(df)}")
print(f"Products: {len(products_df)}  Customers: {len(customers_df)}  Stores: {len(stores_df)}")
print(df.head(3).to_string())
