-- =====================================================================
-- RetailIQ - SQL Analysis Queries (PostgreSQL)
-- =====================================================================
-- These queries run against the normalized schema (schema.sql) and the
-- vw_sales_full view. Grouped by theme; each has a one-line purpose
-- comment - use these directly in interviews to explain your thinking.
-- =====================================================================


-- ---------------------------------------------------------------------
-- SECTION 1: BASIC AGGREGATIONS
-- ---------------------------------------------------------------------

-- 1. Total revenue, profit and orders overall
SELECT
    SUM(sales_amount) AS total_revenue,
    SUM(profit_amount) AS total_profit,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales_amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM vw_sales_full;

-- 2. Top 10 products by revenue
SELECT product_name, category, SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY product_name, category
ORDER BY revenue DESC
LIMIT 10;

-- 3. Bottom 10 products by revenue (candidates for discontinuation)
SELECT product_name, category, SUM(sales_amount) AS revenue, SUM(quantity) AS units_sold
FROM vw_sales_full
GROUP BY product_name, category
ORDER BY revenue ASC
LIMIT 10;

-- 4. Revenue by category
SELECT category, SUM(sales_amount) AS revenue, SUM(profit_amount) AS profit,
       ROUND(SUM(profit_amount) / NULLIF(SUM(sales_amount), 0) * 100, 2) AS margin_pct
FROM vw_sales_full
GROUP BY category
ORDER BY revenue DESC;

-- 5. Revenue by sub-category within each category
SELECT category, sub_category, SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY category, sub_category
ORDER BY category, revenue DESC;

-- 6. Revenue by region
SELECT region, SUM(sales_amount) AS revenue, COUNT(DISTINCT order_id) AS orders
FROM vw_sales_full
GROUP BY region
ORDER BY revenue DESC;

-- 7. Revenue by state
SELECT state, SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY state
ORDER BY revenue DESC;

-- 8. Revenue by city (top 15)
SELECT city, SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY city
ORDER BY revenue DESC
LIMIT 15;

-- 9. Revenue and profit by payment method
SELECT payment_method, SUM(sales_amount) AS revenue, COUNT(DISTINCT order_id) AS orders
FROM vw_sales_full
GROUP BY payment_method
ORDER BY revenue DESC;


-- ---------------------------------------------------------------------
-- SECTION 2: TIME-BASED TRENDS
-- ---------------------------------------------------------------------

-- 10. Monthly sales trend
SELECT year, month, month_name, SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY year, month, month_name
ORDER BY year, month;

-- 11. Quarterly revenue by year
SELECT year, quarter, SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY year, quarter
ORDER BY year, quarter;

-- 12. Year-over-year revenue comparison
SELECT year, SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY year
ORDER BY year;

-- 13. Month-over-month growth % (window function)
WITH monthly AS (
    SELECT year, month, SUM(sales_amount) AS revenue
    FROM vw_sales_full
    GROUP BY year, month
)
SELECT
    year, month, revenue,
    LAG(revenue) OVER (ORDER BY year, month) AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY year, month))
        / NULLIF(LAG(revenue) OVER (ORDER BY year, month), 0) * 100, 2
    ) AS mom_growth_pct
FROM monthly
ORDER BY year, month;

-- 14. 3-month moving average of revenue (window function)
WITH monthly AS (
    SELECT year, month, SUM(sales_amount) AS revenue
    FROM vw_sales_full
    GROUP BY year, month
)
SELECT
    year, month, revenue,
    ROUND(AVG(revenue) OVER (
        ORDER BY year, month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_3m
FROM monthly
ORDER BY year, month;

-- 15. Weekday vs weekend sales comparison
SELECT
    CASE WHEN EXTRACT(DOW FROM order_date) IN (0, 6) THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    SUM(sales_amount) AS revenue,
    COUNT(DISTINCT order_id) AS orders
FROM vw_sales_full
GROUP BY 1;

-- 16. Sales by day of week (seasonality)
SELECT TO_CHAR(order_date, 'Day') AS weekday, SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY 1
ORDER BY revenue DESC;

-- 17. Festive season (Oct-Dec) vs rest of year revenue
SELECT
    CASE WHEN month IN (10, 11, 12) THEN 'Festive (Oct-Dec)' ELSE 'Rest of Year' END AS season,
    SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY 1;


-- ---------------------------------------------------------------------
-- SECTION 3: CUSTOMER ANALYSIS
-- ---------------------------------------------------------------------

-- 18. Top 10 customers by lifetime revenue
SELECT customer_id, customer_name, SUM(sales_amount) AS lifetime_revenue,
       COUNT(DISTINCT order_id) AS total_orders
FROM vw_sales_full
GROUP BY customer_id, customer_name
ORDER BY lifetime_revenue DESC
LIMIT 10;

-- 19. Customer segmentation by total spend (simple RFM-lite tiering)
WITH customer_spend AS (
    SELECT customer_id, customer_name, SUM(sales_amount) AS total_spend,
           COUNT(DISTINCT order_id) AS order_count,
           MAX(order_date) AS last_order_date
    FROM vw_sales_full
    GROUP BY customer_id, customer_name
)
SELECT *,
    CASE
        WHEN total_spend >= 100000 THEN 'Platinum'
        WHEN total_spend >= 50000  THEN 'Gold'
        WHEN total_spend >= 20000  THEN 'Silver'
        ELSE 'Bronze'
    END AS customer_tier
FROM customer_spend
ORDER BY total_spend DESC;

-- 20. Customers who haven't ordered in the last 6 months (churn risk)
SELECT customer_id, customer_name, MAX(order_date) AS last_order_date
FROM vw_sales_full
GROUP BY customer_id, customer_name
HAVING MAX(order_date) < (SELECT MAX(order_date) FROM vw_sales_full) - INTERVAL '6 months'
ORDER BY last_order_date;

-- 21. Average order value per customer
SELECT customer_id, customer_name,
       ROUND(SUM(sales_amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM vw_sales_full
GROUP BY customer_id, customer_name
ORDER BY avg_order_value DESC
LIMIT 10;

-- 22. New vs returning customers per month (subquery)
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_order_date
    FROM vw_sales_full
    GROUP BY customer_id
)
SELECT
    DATE_TRUNC('month', v.order_date) AS month,
    COUNT(DISTINCT CASE WHEN v.order_date = f.first_order_date THEN v.customer_id END) AS new_customers,
    COUNT(DISTINCT CASE WHEN v.order_date != f.first_order_date THEN v.customer_id END) AS returning_customers
FROM vw_sales_full v
JOIN first_order f ON v.customer_id = f.customer_id
GROUP BY 1
ORDER BY 1;


-- ---------------------------------------------------------------------
-- SECTION 4: STORE PERFORMANCE
-- ---------------------------------------------------------------------

-- 23. Store ranking by revenue
SELECT store_id, store_name, region, SUM(sales_amount) AS revenue,
       RANK() OVER (ORDER BY SUM(sales_amount) DESC) AS revenue_rank
FROM vw_sales_full
GROUP BY store_id, store_name, region
ORDER BY revenue_rank;

-- 24. Store performance vs regional average (subquery)
SELECT
    v.store_id, v.store_name, v.region,
    SUM(v.sales_amount) AS store_revenue,
    (SELECT AVG(region_rev) FROM (
        SELECT region, SUM(sales_amount) AS region_rev
        FROM vw_sales_full GROUP BY region
    ) r WHERE r.region = v.region) AS avg_region_revenue
FROM vw_sales_full v
GROUP BY v.store_id, v.store_name, v.region
ORDER BY store_revenue DESC;

-- 25. Worst performing stores (bottom 3 by profit margin)
SELECT store_id, store_name,
       SUM(sales_amount) AS revenue,
       SUM(profit_amount) AS profit,
       ROUND(SUM(profit_amount) / NULLIF(SUM(sales_amount), 0) * 100, 2) AS margin_pct
FROM vw_sales_full
GROUP BY store_id, store_name
ORDER BY margin_pct ASC
LIMIT 3;

-- 26. Store-wise category performance (which store sells what best)
SELECT store_name, category, SUM(sales_amount) AS revenue
FROM vw_sales_full
GROUP BY store_name, category
ORDER BY store_name, revenue DESC;


-- ---------------------------------------------------------------------
-- SECTION 5: PROFIT & DISCOUNT ANALYSIS
-- ---------------------------------------------------------------------

-- 27. Profit distribution by category
SELECT category,
       SUM(profit_amount) AS total_profit,
       ROUND(AVG(profit_amount), 2) AS avg_profit_per_line,
       ROUND(SUM(profit_amount) / NULLIF(SUM(sales_amount),0) * 100, 2) AS margin_pct
FROM vw_sales_full
GROUP BY category
ORDER BY total_profit DESC;

-- 28. Impact of discount bands on revenue and margin
SELECT
    CASE
        WHEN discount = 0 THEN 'No Discount'
        WHEN discount <= 0.10 THEN '1-10%'
        WHEN discount <= 0.20 THEN '11-20%'
        ELSE '20%+'
    END AS discount_band,
    COUNT(*) AS line_items,
    SUM(sales_amount) AS revenue,
    ROUND(AVG(profit_amount), 2) AS avg_profit,
    ROUND(SUM(profit_amount) / NULLIF(SUM(sales_amount), 0) * 100, 2) AS margin_pct
FROM vw_sales_full
GROUP BY 1
ORDER BY discount_band;

-- 29. Products with negative or near-zero margin (pricing problem candidates)
SELECT product_name, category,
       ROUND(AVG(profit_amount) / NULLIF(AVG(sales_amount), 0) * 100, 2) AS avg_margin_pct
FROM vw_sales_full
GROUP BY product_name, category
HAVING AVG(profit_amount) / NULLIF(AVG(sales_amount), 0) < 0.10
ORDER BY avg_margin_pct ASC;

-- 30. High discount + low margin products (potential margin leakage)
SELECT product_name,
       ROUND(AVG(discount) * 100, 1) AS avg_discount_pct,
       ROUND(SUM(profit_amount) / NULLIF(SUM(sales_amount), 0) * 100, 2) AS margin_pct
FROM vw_sales_full
GROUP BY product_name
HAVING AVG(discount) > 0.15
ORDER BY margin_pct ASC
LIMIT 10;


-- ---------------------------------------------------------------------
-- SECTION 6: INVENTORY
-- ---------------------------------------------------------------------

-- 31. Products that need reordering (below reorder level) - any store
SELECT p.product_name, i.store_id, i.stock_quantity, i.reorder_level
FROM inventory i
JOIN products p ON i.product_id = p.product_id
WHERE i.stock_quantity < i.reorder_level
ORDER BY i.stock_quantity ASC;

-- 32. Out-of-stock products by store
SELECT p.product_name, s.store_name
FROM inventory i
JOIN products p ON i.product_id = p.product_id
JOIN stores s ON i.store_id = s.store_id
WHERE i.stock_quantity = 0;

-- 33. Fast-moving products (high sales velocity) vs current stock - reorder priority
WITH recent_sales AS (
    SELECT product_id, SUM(quantity) AS units_sold_last_period
    FROM vw_sales_full
    WHERE order_date >= (SELECT MAX(order_date) FROM vw_sales_full) - INTERVAL '3 months'
    GROUP BY product_id
)
SELECT p.product_name, rs.units_sold_last_period,
       COALESCE(SUM(i.stock_quantity), 0) AS current_total_stock
FROM recent_sales rs
JOIN products p ON rs.product_id = p.product_id
LEFT JOIN inventory i ON i.product_id = p.product_id
GROUP BY p.product_name, rs.units_sold_last_period
ORDER BY rs.units_sold_last_period DESC
LIMIT 10;


-- ---------------------------------------------------------------------
-- SECTION 7: ADVANCED / WINDOW FUNCTIONS / CTEs
-- ---------------------------------------------------------------------

-- 34. Running total (cumulative) revenue by month
WITH monthly AS (
    SELECT year, month, SUM(sales_amount) AS revenue
    FROM vw_sales_full
    GROUP BY year, month
)
SELECT year, month, revenue,
       SUM(revenue) OVER (ORDER BY year, month) AS cumulative_revenue
FROM monthly
ORDER BY year, month;

-- 35. Rank products within each category by revenue (window function + partition)
SELECT category, product_name, SUM(sales_amount) AS revenue,
       RANK() OVER (PARTITION BY category ORDER BY SUM(sales_amount) DESC) AS rank_in_category
FROM vw_sales_full
GROUP BY category, product_name
QUALIFY RANK() OVER (PARTITION BY category ORDER BY SUM(sales_amount) DESC) <= 5;
-- NOTE: QUALIFY is not supported in PostgreSQL - see query 35b for the portable version.

-- 35b. Same as above, portable PostgreSQL version using a CTE instead of QUALIFY
WITH ranked AS (
    SELECT category, product_name, SUM(sales_amount) AS revenue,
           RANK() OVER (PARTITION BY category ORDER BY SUM(sales_amount) DESC) AS rank_in_category
    FROM vw_sales_full
    GROUP BY category, product_name
)
SELECT * FROM ranked WHERE rank_in_category <= 5
ORDER BY category, rank_in_category;

-- 36. Percentage contribution of each category to total revenue
SELECT category,
       SUM(sales_amount) AS revenue,
       ROUND(SUM(sales_amount) * 100.0 / SUM(SUM(sales_amount)) OVER (), 2) AS pct_of_total
FROM vw_sales_full
GROUP BY category
ORDER BY revenue DESC;

-- 37. Customers whose spend is above the overall average (subquery)
SELECT customer_id, customer_name, SUM(sales_amount) AS total_spend
FROM vw_sales_full
GROUP BY customer_id, customer_name
HAVING SUM(sales_amount) > (
    SELECT AVG(customer_total) FROM (
        SELECT SUM(sales_amount) AS customer_total
        FROM vw_sales_full GROUP BY customer_id
    ) t
)
ORDER BY total_spend DESC;

-- 38. First and most recent order date per customer (window functions)
SELECT DISTINCT customer_id, customer_name,
       FIRST_VALUE(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS first_order,
       LAST_VALUE(order_date) OVER (
           PARTITION BY customer_id ORDER BY order_date
           ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
       ) AS last_order
FROM vw_sales_full;

-- 39. Category-wise contribution to profit using a reusable VIEW
CREATE OR REPLACE VIEW vw_category_profit AS
SELECT category, SUM(sales_amount) AS revenue, SUM(profit_amount) AS profit
FROM vw_sales_full
GROUP BY category;

SELECT * FROM vw_category_profit ORDER BY profit DESC;

-- 40. Explain plan example (index usage check - run manually to inspect)
EXPLAIN ANALYZE
SELECT * FROM orders WHERE order_date BETWEEN '2025-01-01' AND '2025-03-31';
