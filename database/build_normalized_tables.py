"""
build_normalized_tables.py
---------------------------
Splits the flat cleaned CSV (data/cleaned/retail_sales_cleaned.csv) into
normalized tables matching schema.sql, ready to be loaded into PostgreSQL
via \\copy (see insert_data.sql).

Output CSVs (in database/load/):
    customers.csv
    stores.csv
    products.csv
    orders.csv
    sales.csv
    inventory.csv
"""

import pandas as pd
import numpy as np
import os

df = pd.read_csv("data/cleaned/retail_sales_cleaned.csv")
os.makedirs("database/load", exist_ok=True)

# ---- customers ----------------------------------------------------------
customers = (
    df[["Customer_ID", "Customer_Name", "City", "State", "Region"]]
    .drop_duplicates(subset="Customer_ID")
    .rename(columns=str.lower)
)
customers.to_csv("database/load/customers.csv", index=False)

# ---- stores ---------------------------------------------------------------
# IMPORTANT: each transaction row's "Region" column is the CUSTOMER's region,
# not the store's - a customer from any region can buy at any store. So we
# must pull each store's own fixed region from the original stores reference
# file generated alongside the raw data, NOT derive it from transaction rows
# (which would incorrectly mix in whichever customer happened to shop there).
stores = pd.read_csv("data/raw/stores_reference.csv").rename(columns=str.lower)
stores.to_csv("database/load/stores.csv", index=False)

# ---- products ---------------------------------------------------------------
# unit_cost isn't in the cleaned flat file directly, so approximate it back
# from Cost / Quantity (this mirrors how a real fresher project would need to
# "reverse engineer" a product master when only a flat transactions extract
# is available).
prod_tmp = df.copy()
prod_tmp["unit_cost"] = (prod_tmp["Cost"] / prod_tmp["Quantity"]).round(2)
products = (
    prod_tmp.groupby("Product_ID")
    .agg(
        product_name=("Product_Name", "first"),
        category=("Category", "first"),
        sub_category=("Sub_Category", "first"),
        unit_price=("Unit_Price", "first"),
        unit_cost=("unit_cost", "median"),
        supplier=("Supplier", "first"),
    )
    .reset_index()
    .rename(columns={"Product_ID": "product_id"})
)
products.to_csv("database/load/products.csv", index=False)

# ---- orders (order header - one row per Order_ID) --------------------------
orders = (
    df.groupby("Order_ID")
    .agg(
        order_date=("Date", "first"),
        customer_id=("Customer_ID", "first"),
        store_id=("Store_ID", "first"),
        payment_method=("Payment_Method", "first"),
    )
    .reset_index()
    .rename(columns={"Order_ID": "order_id"})
)
orders.to_csv("database/load/orders.csv", index=False)

# ---- sales (line item grain) -------------------------------------------------
sales = df[[
    "Order_ID", "Product_ID", "Quantity", "Discount", "Sales", "Cost", "Profit"
]].rename(columns={
    "Order_ID": "order_id",
    "Product_ID": "product_id",
    "Quantity": "quantity",
    "Discount": "discount",
    "Sales": "sales_amount",
    "Cost": "cost_amount",
    "Profit": "profit_amount",
})
sales.to_csv("database/load/sales.csv", index=False)

# ---- inventory (synthetic current snapshot per product/store) ---------------
np.random.seed(7)
inv_rows = []
for _, prod in products.iterrows():
    for _, store in stores.iterrows():
        # not every product is stocked at every store - ~70% coverage
        if np.random.rand() < 0.7:
            inv_rows.append({
                "product_id": prod["product_id"],
                "store_id": store["store_id"],
                "stock_quantity": int(np.random.randint(0, 500)),
                "reorder_level": 50,
            })
inventory = pd.DataFrame(inv_rows)
inventory.to_csv("database/load/inventory.csv", index=False)

print("Normalized tables written to database/load/:")
for name, table in [("customers", customers), ("stores", stores), ("products", products),
                     ("orders", orders), ("sales", sales), ("inventory", inventory)]:
    print(f"  {name}: {len(table)} rows")
