"""
forecasting.py
---------------
Simple, interview-friendly sales forecasting model for RetailIQ.

Approach (deliberately simple - no deep learning):
    1. Aggregate daily transactions into MONTHLY revenue.
    2. Engineer basic time features (month index, month-of-year, quarter,
       lag features).
    3. Train/test split chronologically (last 6 months = test set).
    4. Fit two models - Linear Regression (baseline) and Random Forest
       Regressor (main model) - and compare them with MAE / RMSE / R2.
    5. Forecast the next 6 months and save a prediction chart.

Run:
    python analytics/forecasting.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

OUT_DIR = "reports/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv("data/cleaned/retail_sales_cleaned.csv", parse_dates=["Date"])

# ---- 1. Aggregate to monthly revenue -------------------------------------------
monthly = (
    df.set_index("Date")
    .resample("MS")["Sales"]
    .sum()
    .reset_index()
    .rename(columns={"Sales": "Revenue"})
)
monthly["month_index"] = np.arange(len(monthly))          # 0, 1, 2, ... trend feature
monthly["month_of_year"] = monthly["Date"].dt.month
monthly["quarter"] = monthly["Date"].dt.quarter
monthly["lag_1"] = monthly["Revenue"].shift(1)
monthly["lag_2"] = monthly["Revenue"].shift(2)
monthly["lag_3"] = monthly["Revenue"].shift(3)
monthly = monthly.dropna().reset_index(drop=True)

FEATURES = ["month_index", "month_of_year", "quarter", "lag_1", "lag_2", "lag_3"]
TARGET = "Revenue"

# ---- 2. Chronological train/test split (last 6 months = test) ------------------
TEST_MONTHS = 6
train = monthly.iloc[:-TEST_MONTHS]
test = monthly.iloc[-TEST_MONTHS:]

X_train, y_train = train[FEATURES], train[TARGET]
X_test, y_test = test[FEATURES], test[TARGET]

# ---- 3. Train models -----------------------------------------------------------
lr = LinearRegression()
lr.fit(X_train, y_train)
lr_preds = lr.predict(X_test)

rf = RandomForestRegressor(n_estimators=300, max_depth=6, random_state=42)
rf.fit(X_train, y_train)
rf_preds = rf.predict(X_test)


def evaluate(y_true, y_pred, name):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"{name:20s} | MAE: {mae:12,.2f} | RMSE: {rmse:12,.2f} | R2: {r2:.3f}")
    return mae, rmse, r2


print("=" * 70)
print("MODEL EVALUATION (last 6 months held out as test set)")
print("=" * 70)
evaluate(y_test, lr_preds, "Linear Regression")
rf_mae, rf_rmse, rf_r2 = evaluate(y_test, rf_preds, "Random Forest")

# ---- 4. Forecast next 6 months using Random Forest (best/simplest model) ------
future_rows = []
history = monthly.copy()
last_date = history["Date"].max()

for step in range(1, 7):
    next_date = (last_date + pd.DateOffset(months=step))
    next_month_index = history["month_index"].max() + 1
    next_month_of_year = next_date.month
    next_quarter = (next_date.month - 1) // 3 + 1
    lag_1 = history["Revenue"].iloc[-1]
    lag_2 = history["Revenue"].iloc[-2]
    lag_3 = history["Revenue"].iloc[-3]

    X_next = pd.DataFrame([{
        "month_index": next_month_index,
        "month_of_year": next_month_of_year,
        "quarter": next_quarter,
        "lag_1": lag_1,
        "lag_2": lag_2,
        "lag_3": lag_3,
    }])
    pred_revenue = rf.predict(X_next)[0]

    future_rows.append({"Date": next_date, "Revenue": pred_revenue})
    # append prediction to history so next month's lag features use it
    history = pd.concat([history, pd.DataFrame([{
        "Date": next_date, "Revenue": pred_revenue, "month_index": next_month_index,
        "month_of_year": next_month_of_year, "quarter": next_quarter,
        "lag_1": lag_1, "lag_2": lag_2, "lag_3": lag_3
    }])], ignore_index=True)

forecast_df = pd.DataFrame(future_rows)
forecast_df.to_csv("data/cleaned/sales_forecast_next_6_months.csv", index=False)
print("\nForecast for next 6 months:")
print(forecast_df.to_string(index=False))

# ---- 5. Plot actual vs forecast -------------------------------------------------
plt.figure(figsize=(12, 6))
plt.plot(monthly["Date"], monthly["Revenue"], marker="o", label="Actual Revenue", color="#2563eb")
plt.plot(forecast_df["Date"], forecast_df["Revenue"], marker="o", linestyle="--",
         label="Forecast (Next 6 Months)", color="#f97316")
plt.title("RetailIQ - Monthly Sales Forecast (Random Forest Regression)")
plt.xlabel("Month")
plt.ylabel("Revenue (Rs.)")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "13_sales_forecast.png"), dpi=120)
plt.close()
print(f"\nSaved forecast chart: {OUT_DIR}/13_sales_forecast.png")

# ---- 6. Feature importance chart (explainability - good for interviews) --------
importances = pd.Series(rf.feature_importances_, index=FEATURES).sort_values()
plt.figure(figsize=(8, 5))
importances.plot(kind="barh", color="#059669")
plt.title("Random Forest - Feature Importance")
plt.xlabel("Importance")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "14_feature_importance.png"), dpi=120)
plt.close()
print(f"Saved feature importance chart: {OUT_DIR}/14_feature_importance.png")

print(f"\nFinal model chosen: Random Forest Regressor "
      f"(MAE={rf_mae:,.0f}, RMSE={rf_rmse:,.0f}, R2={rf_r2:.3f})")
