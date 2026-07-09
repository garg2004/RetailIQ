# RetailIQ — Power BI Dashboard Setup Guide

> **A note on this folder:** a `.pbix` file is a binary format only Power BI
> Desktop (Windows) can create, so it can't be generated directly in this
> environment. Instead, this folder gives you everything needed to build the
> exact same dashboard yourself in under 30 minutes: the data to import, the
> data model, every DAX measure, and the visual layout. Follow the steps below
> in order and you'll have `RetailIQ.pbix` ready to save into this folder.

---

## 1. Data source

Import the cleaned dataset directly, OR connect to PostgreSQL once it's set up.

**Option A — Fastest (CSV import):**
`Get Data → Text/CSV → data/cleaned/retail_sales_cleaned.csv`

**Option B — Realistic for interviews (PostgreSQL import):**
`Get Data → PostgreSQL database → server: localhost, database: retailiq`
Import these tables/view: `vw_sales_full`, `inventory`, `products`, `stores`

Option B is what you should describe in interviews — it shows you can connect
BI tools directly to a normalized database instead of just flat files.

---

## 2. Data model (relationships)

If importing via Option B, Power BI will auto-detect these relationships from
foreign keys — verify in **Model view**:

```
customers (1) ──< orders (many)
stores    (1) ──< orders (many)
orders    (1) ──< sales  (many)
products  (1) ──< sales  (many)
products  (1) ──< inventory (many)
stores    (1) ──< inventory (many)
```

If importing the flat CSV (Option A), no relationships are needed — everything
is already denormalized into one table.

Also add a **Date table** (Modeling → New Table):
```
DateTable = CALENDAR(DATE(2023,1,1), DATE(2025,12,31))
```
Mark it as a Date Table (Table tools → Mark as Date Table), then relate
`DateTable[Date]` to `orders[order_date]` (or `Date` column if using the flat CSV).

---

## 3. DAX measures

Create a new table/measure group called `_Measures` and add:

```DAX
Total Revenue = SUM(vw_sales_full[sales_amount])

Total Profit = SUM(vw_sales_full[profit_amount])

Total Orders = DISTINCTCOUNT(vw_sales_full[order_id])

Total Units Sold = SUM(vw_sales_full[quantity])

Avg Order Value = DIVIDE([Total Revenue], [Total Orders])

Profit Margin % = DIVIDE([Total Profit], [Total Revenue])

Revenue LY =
CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(DateTable[Date]))

Revenue Growth % =
DIVIDE([Total Revenue] - [Revenue LY], [Revenue LY])

Revenue MTD =
TOTALMTD([Total Revenue], DateTable[Date])

Revenue Rolling 3M Avg =
AVERAGEX(
    DATESINPERIOD(DateTable[Date], LASTDATE(DateTable[Date]), -3, MONTH),
    [Total Revenue]
)

Top Product Rank =
RANKX(ALL(vw_sales_full[product_name]), [Total Revenue])

Customer Tier =
SWITCH(
    TRUE(),
    [Total Revenue] >= 100000, "Platinum",
    [Total Revenue] >= 50000,  "Gold",
    [Total Revenue] >= 20000,  "Silver",
    "Bronze"
)

Low Stock Flag =
IF(SUM(inventory[stock_quantity]) < SUM(inventory[reorder_level]), "Reorder", "OK")
```

---

## 4. Report pages & visuals

### Page 1 — Executive Overview
- **KPI Cards** (top row): Total Revenue, Total Profit, Total Orders,
  Avg Order Value, Revenue Growth % — use Card or KPI visual with `Revenue LY`
  as the target for the KPI visual's trend arrow.
- **Line Chart**: `DateTable[Date]` (Month) on X-axis, `Total Revenue` and
  `Total Profit` on Y-axis (dual measures, same chart).
- **Map**: `stores[region]` or `customers[state]` bubble-sized by `Total Revenue`.
- **Treemap**: `products[category]` → `products[sub_category]`, sized by
  `Total Revenue`.
- **Bar Chart**: Top 10 `product_name` by `Total Revenue` (Top N filter).
- **Pie Chart**: `Total Revenue` by `region`.

### Page 2 — Store & Customer Deep Dive
- **Bar Chart**: `store_name` by `Total Revenue`, sorted descending.
- **Table**: `customer_name`, `Total Revenue`, `Total Orders`, `Customer Tier`
  — sorted by revenue, Top N = 20.
- **Heatmap (Matrix visual with conditional formatting)**: `store_name` (rows)
  × `Month` (columns), values = `Total Revenue`, background color scale applied.

### Page 3 — Forecast & Inventory
- **Line Chart with forecast**: `Total Revenue` by Month, then use Power BI's
  built-in **Analytics pane → Forecast** (exponential smoothing) for a quick
  native forecast, OR import `data/cleaned/sales_forecast_next_6_months.csv`
  as a second table and plot it alongside actuals (this matches the Random
  Forest model built in `analytics/forecasting.py` — more accurate than
  Power BI's built-in forecast for this seasonal data).
- **Table**: products where `Low Stock Flag = "Reorder"`, conditional
  formatting on `stock_quantity`.

### Slicers (add to every page, sync across pages via View → Sync Slicers)
- `DateTable[Date]` (between slicer)
- `region`
- `store_name`
- `category`
- `customer_name` (searchable slicer)

---

## 5. Formatting checklist

- Apply a consistent theme: View → Themes → import a dark theme (matches the
  web dashboard's "command center" look) or use Power BI's built-in
  **Executive** theme.
- Format all currency measures with `₹` and thousands separators.
- Add a title text box: "RetailIQ — Sales Analytics & Demand Insights".
- Add page navigation buttons (Insert → Buttons → Blank, set action to
  "Page navigation").

---

## 6. Save

`File → Save As → RetailIQ.pbix`, place it in this `powerbi/` folder.

---

## Files in this folder
- `DAX_measures.txt` — plain-text copy of all measures above (copy-paste ready)
- `PowerBI_Setup_Guide.md` — this file
