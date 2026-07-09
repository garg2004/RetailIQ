"""
models.py
----------
SQLAlchemy ORM models mirroring database/schema.sql.
These map Python classes to the PostgreSQL tables so we can query them
using the ORM instead of writing raw SQL strings everywhere in routes.py.
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from api.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(10), primary_key=True)
    customer_name = Column(String(100), nullable=False)
    city = Column(String(50))
    state = Column(String(50))
    region = Column(String(20), nullable=False)


class Store(Base):
    __tablename__ = "stores"

    store_id = Column(String(10), primary_key=True)
    store_name = Column(String(100), nullable=False)
    region = Column(String(20), nullable=False)


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(10), primary_key=True)
    product_name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    sub_category = Column(String(50), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    supplier = Column(String(100))


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(15), primary_key=True)
    order_date = Column(Date, nullable=False)
    customer_id = Column(String(10), ForeignKey("customers.customer_id"), nullable=False)
    store_id = Column(String(10), ForeignKey("stores.store_id"), nullable=False)
    payment_method = Column(String(30))


class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(15), ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(String(10), ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    discount = Column(Numeric(4, 2), default=0)
    sales_amount = Column(Numeric(12, 2), nullable=False)
    cost_amount = Column(Numeric(12, 2), nullable=False)
    profit_amount = Column(Numeric(12, 2), nullable=False)


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(10), ForeignKey("products.product_id"), nullable=False)
    store_id = Column(String(10), ForeignKey("stores.store_id"), nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    reorder_level = Column(Integer, nullable=False, default=50)
    last_updated = Column(TIMESTAMP, server_default=func.now())
