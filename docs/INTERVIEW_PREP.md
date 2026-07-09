# RetailIQ — Interview Preparation Guide

This document gives you a ready-to-use explanation of the project plus
likely interview questions across every skill area it touches, with
STAR-format (Situation, Task, Action, Result) answers you can adapt in your
own words. **Don't memorize these verbatim — read them, understand the
"why" behind each decision, then explain it naturally.**

---

## 1. Project Explanation (30-second version)

> "RetailIQ is an end-to-end retail analytics platform I built to simulate
> how a real retail business would go from raw, messy sales data to
> decision-ready insights. I generated a realistic ~60,000-row synthetic
> dataset with the kinds of data quality problems you actually see in the
> field — missing values, duplicates, bad date formats — then built a
> Pandas cleaning pipeline, a normalized PostgreSQL schema, 40 SQL analysis
> queries, a Random Forest forecasting model, a FastAPI backend, and both a
> Power BI dashboard and a custom web dashboard on top of it."

## 2. Architecture Explanation (2-minute version)

> "I structured it as a pipeline: raw CSV → Pandas cleaning script → cleaned
> CSV → PostgreSQL (normalized into customers, products, stores, orders, and
> sales tables with proper foreign keys) → a FastAPI layer that exposes
> analytics as REST endpoints → two presentation layers, Power BI for
> executive reporting and a lightweight web dashboard for a live, filterable
> view. Machine learning sits alongside the SQL analysis — I aggregate to
> monthly revenue, engineer lag and seasonality features, and use a Random
> Forest Regressor to forecast the next 6 months, comparing it against a
> Linear Regression baseline so I can justify the model choice with actual
> numbers (R² of 0.99 vs 0.71)."

---

## 3. Technical Questions

**Q: Why PostgreSQL over MySQL or a NoSQL database?**
A: The data is inherently relational — customers, products, stores, and
orders all reference each other, and I need strong consistency (foreign
keys, transactions) plus window functions and CTEs for the analytical
queries. PostgreSQL has excellent support for both OLTP-style constraints
and OLAP-style analytical SQL in one engine, which fits a fresher-scale
project without needing a separate warehouse.

**Q: Why FastAPI instead of Flask or Django?**
A: FastAPI gives me automatic request validation (via Pydantic/type hints),
auto-generated Swagger docs at `/docs` for free, and async support if I ever
need it — with less boilerplate than Django and better built-in validation
than plain Flask.

**Q: Why did you build a "demo mode" with SQLite alongside PostgreSQL?**
A: So the API can be run and tested with zero external setup — useful for
quick local testing or for someone reviewing the project without wanting to
install Postgres first. In real deployment I'd always point it at Postgres
(`DEMO_MODE=false`); the SQL in `routes.py` intentionally avoids
Postgres-only syntax so it works identically against both.

**Q: How would you scale this to millions of rows?**
A: Add indexes on the columns actually used in WHERE/JOIN clauses (already
done for `order_date`, `customer_id`, `product_id`, etc.), consider
partitioning the `sales` table by month, add a caching layer (Redis) in
front of the FastAPI endpoints for expensive aggregations, and move heavy
recurring aggregations into materialized views refreshed on a schedule
instead of computing them on every API call.

**Q: What was the hardest data quality issue to fix?**
A: Outliers in the `Sales` column. A single global IQR bound was too
aggressive because Electronics and Grocery have wildly different price
ranges — a legitimate ₹80,000 laptop order looked like an "outlier" next to
₹50 grocery items. I fixed it by applying IQR capping **per category**
instead of globally, which is a good example of why you always sanity-check
automated cleaning rules against the actual business context.

---

## 4. Business Questions

**Q: Which products should be discontinued?**
A: Query #3 (bottom 10 products by revenue) combined with query #29
(products with near-zero or negative margin) — a product only gets flagged
if it's both low-revenue AND low-margin, not just low-volume (a
low-volume/high-margin niche product might still be worth keeping).

**Q: How do you identify underperforming stores?**
A: Not just by raw revenue — query #25 ranks stores by **profit margin**,
and query #24 compares each store's revenue against its regional average.
A store can have high revenue but poor margin due to excessive discounting,
which raw revenue ranking alone would hide.

**Q: What inventory should be reordered first?**
A: Query #33 cross-references recent sales velocity (last 3 months) against
current stock levels — a fast-moving product that's low on stock is a much
higher priority than a slow-moving product that happens to be below its
static reorder threshold.

---

## 5. SQL Questions

**Q: Write a query to find the top 3 products per category.**
A: See query #35b in `database/analysis_queries.sql` — uses `RANK() OVER
(PARTITION BY category ORDER BY revenue DESC)` inside a CTE, then filters
`WHERE rank <= 3` in the outer query (PostgreSQL doesn't support `QUALIFY`,
unlike Snowflake/BigQuery, so you need the CTE wrapper).

**Q: What's the difference between RANK(), DENSE_RANK(), and ROW_NUMBER()?**
A: `ROW_NUMBER()` always gives unique sequential numbers even for ties.
`RANK()` gives ties the same rank but skips subsequent numbers (1,1,3).
`DENSE_RANK()` gives ties the same rank without skipping (1,1,2).

**Q: Explain the difference between a CTE and a subquery.**
A: Functionally similar, but a CTE (`WITH x AS (...)`) is more readable for
multi-step logic and can be referenced multiple times in the outer query
without repeating the logic — I used CTEs for the moving average and
cumulative revenue queries specifically for that reuse and readability.

**Q: Why use a VIEW (`vw_sales_full`) instead of repeating the JOINs
everywhere?**
A: DRY principle — the JOIN across sales/orders/customers/stores/products is
identical for almost every analytical query, so wrapping it once in a view
means every query (and the Power BI import) reads from a single, tested
source instead of risking a subtly different JOIN each time.

---

## 6. Power BI Questions

**Q: How do slicers stay in sync across report pages?**
A: `View → Sync Slicers` pane — check the boxes for each page you want a
slicer to filter, even if the slicer visual itself isn't placed on that page.

**Q: How would you show YoY growth in Power BI?**
A: A DAX measure using `SAMEPERIODLASTYEAR()` inside a `CALCULATE()` (see
`Revenue LY` measure), then a `DIVIDE()` measure for the growth percentage.
Requires a proper marked Date table for time intelligence functions to work.

**Q: Star schema vs. flat table — which did you use and why?**
A: I documented both approaches (see `PowerBI_Setup_Guide.md`) — a proper
star schema (importing `customers`, `products`, `stores`, `orders`, `sales`
as separate related tables) is what I'd defend in an interview, since it's
more efficient and scales better than one denormalized flat table, even
though the flat CSV import is faster to demo.

---

## 7. Python Questions

**Q: Why fillna with the mode/median instead of dropping rows with missing
values?**
A: Missing values were a small percentage (1-2%) of non-critical fields
(Customer_Name, City, Discount, Payment_Method) - dropping rows would lose
real transaction data unnecessarily. I only dropped rows for truly unusable
data (unparsable dates), since there's no reasonable way to impute a
transaction date.

**Q: Walk me through your IQR outlier logic.**
A: `Q1` and `Q3` are the 25th/75th percentiles, `IQR = Q3 - Q1`. Anything
below `Q1 - 1.5*IQR` or above `Q3 + 1.5*IQR` is flagged. I applied this
per-category using `groupby("Category").transform()` rather than globally,
and capped (clipped) rather than dropped the outliers, since dropping
entire rows would also throw away otherwise-valid Quantity/Customer data
tied to that transaction.

**Q: Why `.astype(object)` before mixing strings and numbers in a column?**
A: Pandas raises a `LossySetitemError` if you try to assign a string into an
`int64` column in place — converting the column to a generic `object` dtype
first allows mixed types during the intentional "dirtying" step (simulating
data-entry mistakes like `"2 units"` instead of `2`).

---

## 8. Machine Learning Questions

**Q: Why Random Forest over Linear Regression for forecasting?**
A: I trained both and compared them on an honest chronological holdout (last
6 months, not a random split, since shuffling time series data leaks future
information into training). Linear Regression scored R²≈0.71 because it
can't capture non-linear seasonal patterns as well; Random Forest scored
R²≈0.99 by combining trend, month-of-year, quarter, and lag features
non-linearly.

**Q: Why lag features and not just date/month as features?**
A: Lag features (`lag_1`, `lag_2`, `lag_3` = revenue from the previous 1-3
months) let the model learn momentum and autocorrelation in the series,
which a month-of-year feature alone can't capture — e.g. a recent
month-over-month uptick tends to continue short-term.

**Q: How did you avoid data leakage in the forecast?**
A: Chronological train/test split (never random shuffling for time series),
and when generating the actual 6-month-ahead forecast, each new month's
prediction is appended to history and used as the lag input for the next
month — an honest simulation of "we don't know the future when we predict
it," rather than leaking real future values into the lag features.

**Q: What are MAE, RMSE, and R² telling you here, and why report all three?**
A: MAE is the average absolute error in revenue units (easy to explain to a
business stakeholder — "off by ~₹6L on average"). RMSE penalizes large
errors more heavily (useful to check for occasional big misses). R² tells
you the proportion of variance explained — useful for comparing models on a
single normalized number. I report all three because a business decision
usually cares about MAE (money) more than R², but R² is what you'd quote to
another data scientist to compare model quality quickly.

---

## Final tip

Every number, chart, and query in this project came from the scripts in this
repo — re-run them yourself before an interview
(`python analytics/generate_dataset.py && python analytics/cleaning.py &&
python analytics/analysis.py && python analytics/forecasting.py`) so the
figures you quote are always fresh and you can speak to them confidently.
