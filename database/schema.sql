-- =====================================================================
-- RetailIQ Database Schema (PostgreSQL)
-- =====================================================================
-- Normalized to 3NF: separate dimension tables (Customers, Products,
-- Stores) referenced by a central fact table (Sales / Orders).
-- =====================================================================

DROP TABLE IF EXISTS sales CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS stores CASCADE;

-- ---------------------------------------------------------------------
-- Dimension: Customers
-- ---------------------------------------------------------------------
CREATE TABLE customers (
    customer_id     VARCHAR(10)  PRIMARY KEY,
    customer_name   VARCHAR(100) NOT NULL,
    city            VARCHAR(50),
    state           VARCHAR(50),
    region          VARCHAR(20)  NOT NULL
);

-- ---------------------------------------------------------------------
-- Dimension: Stores
-- ---------------------------------------------------------------------
CREATE TABLE stores (
    store_id        VARCHAR(10)  PRIMARY KEY,
    store_name      VARCHAR(100) NOT NULL,
    region          VARCHAR(20)  NOT NULL
);

-- ---------------------------------------------------------------------
-- Dimension: Products
-- ---------------------------------------------------------------------
CREATE TABLE products (
    product_id      VARCHAR(10)  PRIMARY KEY,
    product_name    VARCHAR(150) NOT NULL,
    category        VARCHAR(50)  NOT NULL,
    sub_category    VARCHAR(50)  NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    unit_cost       NUMERIC(10,2) NOT NULL CHECK (unit_cost >= 0),
    supplier        VARCHAR(100)
);

-- ---------------------------------------------------------------------
-- Fact: Orders (order header - one row per Order_ID)
-- ---------------------------------------------------------------------
CREATE TABLE orders (
    order_id        VARCHAR(15)  PRIMARY KEY,
    order_date      DATE         NOT NULL,
    customer_id     VARCHAR(10)  NOT NULL REFERENCES customers(customer_id),
    store_id        VARCHAR(10)  NOT NULL REFERENCES stores(store_id),
    payment_method  VARCHAR(30)
);

-- ---------------------------------------------------------------------
-- Fact: Sales (line-item grain - one row per product sold per order)
-- ---------------------------------------------------------------------
CREATE TABLE sales (
    sale_id         SERIAL PRIMARY KEY,
    order_id        VARCHAR(15) NOT NULL REFERENCES orders(order_id),
    product_id      VARCHAR(10) NOT NULL REFERENCES products(product_id),
    quantity        INTEGER      NOT NULL CHECK (quantity > 0),
    discount        NUMERIC(4,2) DEFAULT 0 CHECK (discount >= 0 AND discount <= 1),
    sales_amount    NUMERIC(12,2) NOT NULL CHECK (sales_amount >= 0),
    cost_amount     NUMERIC(12,2) NOT NULL CHECK (cost_amount >= 0),
    profit_amount   NUMERIC(12,2) NOT NULL
);

-- ---------------------------------------------------------------------
-- Inventory (current stock snapshot per product per store)
-- ---------------------------------------------------------------------
CREATE TABLE inventory (
    inventory_id     SERIAL PRIMARY KEY,
    product_id       VARCHAR(10) NOT NULL REFERENCES products(product_id),
    store_id         VARCHAR(10) NOT NULL REFERENCES stores(store_id),
    stock_quantity   INTEGER NOT NULL CHECK (stock_quantity >= 0),
    reorder_level    INTEGER NOT NULL DEFAULT 50,
    last_updated     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, store_id)
);

-- =====================================================================
-- Indexes (for the query patterns used in analysis.sql / FastAPI)
-- =====================================================================
CREATE INDEX idx_orders_date            ON orders(order_date);
CREATE INDEX idx_orders_customer        ON orders(customer_id);
CREATE INDEX idx_orders_store           ON orders(store_id);

CREATE INDEX idx_sales_order            ON sales(order_id);
CREATE INDEX idx_sales_product          ON sales(product_id);

CREATE INDEX idx_products_category      ON products(category);
CREATE INDEX idx_customers_region       ON customers(region);
CREATE INDEX idx_inventory_product_store ON inventory(product_id, store_id);

-- =====================================================================
-- A convenience VIEW that flattens sales + orders + products + customers
-- + stores into one wide table - this is what most BI/reporting queries
-- and the Power BI dashboard will query against.
-- =====================================================================
CREATE OR REPLACE VIEW vw_sales_full AS
SELECT
    s.sale_id,
    o.order_id,
    o.order_date,
    EXTRACT(YEAR FROM o.order_date)::INT      AS year,
    EXTRACT(MONTH FROM o.order_date)::INT     AS month,
    TO_CHAR(o.order_date, 'Mon')              AS month_name,
    EXTRACT(QUARTER FROM o.order_date)::INT   AS quarter,
    c.customer_id,
    c.customer_name,
    c.city,
    c.state,
    c.region,
    st.store_id,
    st.store_name,
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    s.quantity,
    p.unit_price,
    s.discount,
    s.sales_amount,
    s.cost_amount,
    s.profit_amount,
    o.payment_method
FROM sales s
JOIN orders o    ON s.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
JOIN stores st   ON o.store_id = st.store_id
JOIN products p  ON s.product_id = p.product_id;
