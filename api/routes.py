"""
routes.py
----------
All REST API endpoints for the RetailIQ backend.

Endpoints:
    GET /dashboard          - overall KPI summary
    GET /sales              - sales records (paginated, filterable)
    GET /sales/monthly      - monthly revenue trend
    GET /products           - product catalogue
    GET /products/top       - top N products by revenue
    GET /customers          - customer list
    GET /customers/top      - top N customers by revenue
    GET /stores             - store performance
    GET /inventory          - inventory status
    GET /inventory/reorder  - products below reorder level
    GET /forecast           - next 6 months sales forecast

Notes:
    - Uses raw parameterized SQL via SQLAlchemy `text()` for clarity and
      because these are analytics/reporting queries (arguably easier to
      read as SQL than as heavy ORM query-builder chains).
    - Works against SQLite (DEMO_MODE) or PostgreSQL identically since we
      stick to standard SQL only (no Postgres-only syntax here).
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import pandas as pd
import os

from api.database import get_db

router = APIRouter()


# ---------------------------------------------------------------------
# /dashboard - high level KPIs
# ---------------------------------------------------------------------
@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT
            SUM(sales_amount) AS total_revenue,
            SUM(profit_amount) AS total_profit,
            COUNT(DISTINCT order_id) AS total_orders,
            SUM(quantity) AS total_units_sold
        FROM sales
    """)).mappings().first()

    total_revenue = row["total_revenue"] or 0
    total_orders = row["total_orders"] or 1

    return {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(row["total_profit"] or 0, 2),
        "total_orders": row["total_orders"] or 0,
        "total_units_sold": row["total_units_sold"] or 0,
        "average_order_value": round(total_revenue / total_orders, 2),
    }


# ---------------------------------------------------------------------
# /sales - paginated raw sales records with optional filters
# ---------------------------------------------------------------------
@router.get("/sales")
def get_sales(
    region: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    filters = []
    params = {}

    if region:
        filters.append("c.region = :region")
        params["region"] = region
    if category:
        filters.append("p.category = :category")
        params["category"] = category
    if start_date:
        filters.append("o.order_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("o.order_date <= :end_date")
        params["end_date"] = end_date

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    query = text(f"""
        SELECT o.order_id, o.order_date, c.customer_name, c.region,
               p.product_name, p.category, s.quantity, s.sales_amount, s.profit_amount
        FROM sales s
        JOIN orders o ON s.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products p ON s.product_id = p.product_id
        {where_clause}
        ORDER BY o.order_date DESC
        LIMIT :limit OFFSET :offset
    """)
    rows = db.execute(query, params).mappings().all()
    return {"page": page, "page_size": page_size, "results": [dict(r) for r in rows]}


# ---------------------------------------------------------------------
# /sales/monthly - monthly revenue trend
# ---------------------------------------------------------------------
@router.get("/sales/monthly")
def get_monthly_sales(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT o.order_date, s.sales_amount, s.profit_amount
        FROM sales s JOIN orders o ON s.order_id = o.order_id
    """)).mappings().all()

    df = pd.DataFrame(rows)
    df["order_date"] = pd.to_datetime(df["order_date"])
    monthly = (
        df.set_index("order_date")
        .resample("MS")[["sales_amount", "profit_amount"]]
        .sum()
        .reset_index()
    )
    monthly["order_date"] = monthly["order_date"].dt.strftime("%Y-%m")
    return monthly.to_dict(orient="records")


# ---------------------------------------------------------------------
# /products - full product catalogue
# ---------------------------------------------------------------------
@router.get("/products")
def get_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = "SELECT * FROM products"
    params = {}
    if category:
        query += " WHERE category = :category"
        params["category"] = category
    rows = db.execute(text(query), params).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# /products/top - top N products by revenue
# ---------------------------------------------------------------------
@router.get("/products/top")
def get_top_products(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT p.product_name, p.category, SUM(s.sales_amount) AS revenue,
               SUM(s.quantity) AS units_sold
        FROM sales s JOIN products p ON s.product_id = p.product_id
        GROUP BY p.product_name, p.category
        ORDER BY revenue DESC
        LIMIT :limit
    """), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# /customers - customer list
# ---------------------------------------------------------------------
@router.get("/customers")
def get_customers(region: Optional[str] = None, db: Session = Depends(get_db)):
    query = "SELECT * FROM customers"
    params = {}
    if region:
        query += " WHERE region = :region"
        params["region"] = region
    rows = db.execute(text(query), params).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# /customers/top - top N customers by lifetime revenue
# ---------------------------------------------------------------------
@router.get("/customers/top")
def get_top_customers(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT c.customer_id, c.customer_name, c.region,
               SUM(s.sales_amount) AS lifetime_revenue,
               COUNT(DISTINCT s.order_id) AS total_orders
        FROM sales s
        JOIN orders o ON s.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.customer_id, c.customer_name, c.region
        ORDER BY lifetime_revenue DESC
        LIMIT :limit
    """), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# /stores - store-level performance
# ---------------------------------------------------------------------
@router.get("/stores")
def get_stores(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT st.store_id, st.store_name, st.region,
               SUM(s.sales_amount) AS revenue,
               SUM(s.profit_amount) AS profit,
               COUNT(DISTINCT s.order_id) AS total_orders
        FROM sales s
        JOIN orders o ON s.order_id = o.order_id
        JOIN stores st ON o.store_id = st.store_id
        GROUP BY st.store_id, st.store_name, st.region
        ORDER BY revenue DESC
    """)).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# /inventory - current stock levels
# ---------------------------------------------------------------------
@router.get("/inventory")
def get_inventory(store_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = """
        SELECT i.inventory_id, p.product_name, p.category, i.store_id,
               i.stock_quantity, i.reorder_level
        FROM inventory i JOIN products p ON i.product_id = p.product_id
    """
    params = {}
    if store_id:
        query += " WHERE i.store_id = :store_id"
        params["store_id"] = store_id
    rows = db.execute(text(query), params).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# /inventory/reorder - products below reorder threshold
# ---------------------------------------------------------------------
@router.get("/inventory/reorder")
def get_reorder_list(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT p.product_name, i.store_id, i.stock_quantity, i.reorder_level
        FROM inventory i JOIN products p ON i.product_id = p.product_id
        WHERE i.stock_quantity < i.reorder_level
        ORDER BY i.stock_quantity ASC
    """)).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# /forecast - next 6 months sales forecast (precomputed by forecasting.py)
# ---------------------------------------------------------------------
@router.get("/forecast")
def get_forecast():
    path = "data/cleaned/sales_forecast_next_6_months.csv"
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="Forecast not found. Run `python analytics/forecasting.py` first.",
        )
    df = pd.read_csv(path)
    return df.to_dict(orient="records")
