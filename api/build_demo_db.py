"""
build_demo_db.py
------------------
Builds retailiq_demo.db (SQLite) from the normalized CSVs in
database/load/, mirroring database/schema.sql, purely so the FastAPI
app can be run and tested with zero setup (DEMO_MODE=true default).

For real usage, load PostgreSQL using database/schema.sql +
database/insert_data.sql instead - see README.md.

Run from project root:
    python api/build_demo_db.py
"""

import pandas as pd
import sqlite3
import os

DB_PATH = "retailiq_demo.db"
LOAD_DIR = "database/load"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)

tables = ["customers", "stores", "products", "orders", "sales", "inventory"]
for t in tables:
    df = pd.read_csv(os.path.join(LOAD_DIR, f"{t}.csv"))
    df.to_sql(t, conn, if_exists="replace", index=False)
    print(f"Loaded {t}: {len(df)} rows")

conn.close()
print(f"\nDemo SQLite database built at ./{DB_PATH}")
