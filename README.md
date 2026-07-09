# RetailIQ — Sales Analytics & Demand Insights Dashboard

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?logo=powerbi&logoColor=black)
![scikit-learn](https://img.shields.io/badge/scikit--learn-RandomForest-F7931E?logo=scikitlearn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

An end-to-end, portfolio-grade retail analytics platform: synthetic dataset
generation → PostgreSQL warehouse → Python data cleaning & EDA → SQL analysis
→ machine learning sales forecasting → FastAPI backend → Power BI + web
dashboards.

Built to be **fully understandable and defensible in interviews** — no
Kafka, Spark, Airflow, or Kubernetes. Just the tools a Data Analyst / Junior
Data Engineer / BI Developer would realistically use on the job.

---

## 📌 Project Overview

**Business problem:** A retail company (RetailIQ) has thousands of sales
transactions spread across spreadsheets with no clean way to answer basic
business questions — which products sell, which stores underperform, what
inventory needs reordering, and what next quarter's sales will look like.

**What this project delivers:**
- A normalized PostgreSQL database (customers, products, stores, orders, sales, inventory)
- A repeatable Python data-cleaning pipeline (handles real messy-data problems)
- 40 SQL analysis queries covering aggregations, window functions, CTEs, and views
- Full EDA with 12+ charts answering every business question in the brief
- A Random Forest sales forecasting model (with a Linear Regression baseline for comparison)
- A REST API (FastAPI) exposing all of the above as JSON endpoints
- A Power BI executive dashboard (setup guide + DAX measures included)
- A lightweight dark-themed web dashboard (HTML/Bootstrap/Chart.js) consuming the API

---

## 🏗️ Architecture

```
                     ┌─────────────────────┐
                     │   Raw Retail Data    │  (synthetic, 60k+ rows,
                     │   (CSV, "dirty")     │   intentionally messy)
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │  analytics/cleaning.py│  Pandas cleaning pipeline
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │  Cleaned CSV          │
                     └──────────┬───────────┘
                 ┌──────────────┼──────────────────┐
                 │              │                  │
       ┌─────────▼───────┐ ┌────▼─────────┐ ┌──────▼───────────┐
       │ PostgreSQL DB     │ │ analysis.py  │ │ forecasting.py    │
       │ (normalized       │ │ (EDA charts) │ │ (Random Forest    │
       │  schema + view)   │ │              │ │  forecast model)  │
       └─────────┬─────────┘ └──────────────┘ └───────────────────┘
                 │
       ┌─────────▼─────────┐
       │  FastAPI Backend   │  REST endpoints: /dashboard /sales /products
       │  (api/main.py)     │  /customers /stores /inventory /forecast
       └─────────┬─────────┘
                 │
      ┌──────────┴───────────┐
      │                       │
┌─────▼─────────┐   ┌─────────▼────────────┐
│ Power BI       │   │  Web Dashboard        │
│ Executive      │   │  (HTML/Bootstrap/     │
│ Dashboard      │   │   Chart.js)           │
└────────────────┘   └───────────────────────┘
```

---

## 📁 Folder Structure

```
RetailIQ/
├── data/
│   ├── raw/                    # synthetic raw dataset + reference tables
│   └── cleaned/                # cleaned dataset + forecast output
├── database/
│   ├── schema.sql               # normalized PostgreSQL schema + view
│   ├── insert_data.sql          # \copy bulk load script
│   ├── build_normalized_tables.py  # splits cleaned CSV into star-schema CSVs
│   └── analysis_queries.sql     # 40 SQL analysis queries
├── notebooks/
│   ├── data_cleaning.ipynb
│   ├── exploratory_analysis.ipynb
│   └── forecasting.ipynb
├── analytics/
│   ├── generate_dataset.py      # synthetic data generator
│   ├── cleaning.py              # production cleaning script
│   ├── analysis.py              # EDA script (generates all charts)
│   └── forecasting.py           # Random Forest forecasting script
├── api/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── routes.py                # all REST endpoints
│   ├── database.py              # DB connection (Postgres or SQLite demo mode)
│   ├── models.py                # SQLAlchemy ORM models
│   └── build_demo_db.py         # zero-setup SQLite demo DB builder
├── powerbi/
│   ├── PowerBI_Setup_Guide.md   # step-by-step .pbix build guide
│   └── DAX_measures.txt         # copy-paste DAX measures
├── dashboard/
│   ├── html/index.html
│   ├── css/style.css
│   └── js/app.js
├── reports/
│   ├── screenshots/              # all EDA + forecast charts (PNG)
│   └── data_quality_report.txt   # auto-generated by cleaning.py
├── docs/
│   └── INTERVIEW_PREP.md         # interview questions + STAR answers
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Database | PostgreSQL 16 (SQLite fallback for zero-setup demo) |
| Data Processing | Pandas, NumPy |
| Visualization (EDA) | Matplotlib, Seaborn |
| Machine Learning | scikit-learn (Linear Regression, Random Forest) |
| Backend API | FastAPI, SQLAlchemy, Uvicorn |
| BI Dashboard | Power BI |
| Web Dashboard | HTML, Bootstrap 5, Chart.js, vanilla JavaScript |
| Dev Tools | VS Code, Git, GitHub, Postman |

---

## 🚀 Installation & Setup

### 1. Clone and install dependencies
```bash
git clone https://github.com/<your-username>/RetailIQ.git
cd RetailIQ
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate the dataset
```bash
python analytics/generate_dataset.py     # creates data/raw/retail_sales_raw.csv
python analytics/cleaning.py             # creates data/cleaned/retail_sales_cleaned.csv
```

### 3. Run EDA and forecasting
```bash
python analytics/analysis.py             # charts saved to reports/screenshots/
python analytics/forecasting.py          # forecast + model evaluation
```

### 4a. Quick demo (no database install needed)
```bash
python database/build_normalized_tables.py   # splits cleaned data into star schema CSVs
python api/build_demo_db.py                  # builds a local SQLite demo DB
uvicorn api.main:app --reload --port 8000    # DEMO_MODE=true by default
```
Open **http://localhost:8000/docs** for interactive Swagger API docs.

### 4b. Full PostgreSQL setup (recommended for interviews)
```bash
createdb retailiq
psql -U postgres -d retailiq -f database/schema.sql
python database/build_normalized_tables.py
psql -U postgres -d retailiq -f database/insert_data.sql
cp .env.example .env      # then edit .env: set DEMO_MODE=false + your DB credentials
uvicorn api.main:app --reload --port 8000
```

### 5. Open the web dashboard
With the API running, open `dashboard/html/index.html` directly in a browser
(or serve it: `python -m http.server 5500` from the `dashboard/html` folder).

### 6. Power BI dashboard
See `powerbi/PowerBI_Setup_Guide.md` for a full step-by-step walkthrough
(data model, DAX measures, visuals, slicers).

### 7. Notebooks
```bash
jupyter notebook notebooks/
```
All three notebooks (`data_cleaning`, `exploratory_analysis`, `forecasting`)
run end-to-end and mirror the corresponding scripts in `analytics/`.

---

## 📊 Sample Insights

- Random Forest forecasting achieves **R² ≈ 0.99** on a 6-month chronological
  holdout, vs. R² ≈ 0.71 for a Linear Regression baseline — the seasonality
  and lag features matter a lot for this dataset.
- Electronics is consistently the highest-revenue category but has some of
  the lowest-margin products once discount bands exceed 20%.
- A handful of stores post similar revenue but meaningfully different profit
  margins — a good discussion point on cost control vs. top-line growth.

See `reports/screenshots/` for all 14 charts (monthly trend, category/region
revenue, top/worst products, store comparison, customer segmentation, profit
distribution, discount impact, correlation heatmap, seasonality, forecast,
and feature importance).

---

## 🔮 Future Improvements

- Containerize the API with Docker and add a `docker-compose.yml` for Postgres + API together
- Add authentication (JWT) to the FastAPI backend for multi-user access
- Add CI/CD (GitHub Actions) to run the cleaning + tests on every push
- Swap the flat CSV ingestion for a scheduled ETL job (even a simple cron + script is a good next step before reaching for Airflow)
- Add unit tests (pytest) for the cleaning pipeline and API endpoints
- Extend the forecasting model to per-category or per-store forecasts

---

## 📄 License

MIT — free to use and adapt for your own portfolio.

---

## 🎤 Interview Preparation

See [`docs/INTERVIEW_PREP.md`](docs/INTERVIEW_PREP.md) for a full set of
technical, business, SQL, Power BI, Python, and ML interview questions with
STAR-format answers based on this exact project.
