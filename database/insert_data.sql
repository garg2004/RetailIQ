-- =====================================================================
-- RetailIQ: Data Loading Script
-- =====================================================================
-- Run this AFTER schema.sql, from the RetailIQ/ project root, using:
--     psql -U postgres -d retailiq -f database/insert_data.sql
--
-- We use \copy (client-side, works with psql without server file
-- permissions) to bulk-load the normalized CSVs produced by
-- database/build_normalized_tables.py. This is the realistic way a
-- fresher would load ~60k rows - not writing 60,000 manual INSERTs.
-- =====================================================================

-- Order matters: dimension tables first, then fact tables (FK constraints)

\copy customers(customer_id, customer_name, city, state, region) FROM 'database/load/customers.csv' WITH (FORMAT csv, HEADER true);

\copy stores(store_id, store_name, region) FROM 'database/load/stores.csv' WITH (FORMAT csv, HEADER true);

\copy products(product_id, product_name, category, sub_category, unit_price, unit_cost, supplier) FROM 'database/load/products.csv' WITH (FORMAT csv, HEADER true);

\copy orders(order_id, order_date, customer_id, store_id, payment_method) FROM 'database/load/orders.csv' WITH (FORMAT csv, HEADER true);

\copy sales(order_id, product_id, quantity, discount, sales_amount, cost_amount, profit_amount) FROM 'database/load/sales.csv' WITH (FORMAT csv, HEADER true);

\copy inventory(product_id, store_id, stock_quantity, reorder_level) FROM 'database/load/inventory.csv' WITH (FORMAT csv, HEADER true);

-- Sanity checks after load
SELECT 'customers' AS table_name, COUNT(*) FROM customers
UNION ALL SELECT 'stores', COUNT(*) FROM stores
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'sales', COUNT(*) FROM sales
UNION ALL SELECT 'inventory', COUNT(*) FROM inventory;

-- =====================================================================
-- Sample manual INSERT statements (for reference / interview walk-through)
-- =====================================================================
-- This is what a single order "looks like" going into the normalized
-- schema, useful to explain in an interview even though bulk data is
-- loaded via \copy above.

-- INSERT INTO customers (customer_id, customer_name, city, state, region)
-- VALUES ('CUST00001', 'Aarav Sharma', 'Jaipur', 'Rajasthan', 'West');

-- INSERT INTO stores (store_id, store_name, region)
-- VALUES ('ST008', 'RetailIQ Jaipur Malviya Nagar', 'West');

-- INSERT INTO products (product_id, product_name, category, sub_category, unit_price, unit_cost, supplier)
-- VALUES ('PRD00001', 'Mobiles Electronics Model-1', 'Electronics', 'Mobiles', 15999.00, 11200.00, 'TechDistro Pvt Ltd');

-- INSERT INTO orders (order_id, order_date, customer_id, store_id, payment_method)
-- VALUES ('ORD000001', '2025-01-15', 'CUST00001', 'ST008', 'UPI');

-- INSERT INTO sales (order_id, product_id, quantity, discount, sales_amount, cost_amount, profit_amount)
-- VALUES ('ORD000001', 'PRD00001', 1, 0.10, 14399.10, 11200.00, 3199.10);
