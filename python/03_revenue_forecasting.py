"""
03_revenue_forecasting.py
Time-series analysis and forecasting on monthly e-commerce revenue.
Fits a trend + seasonal regression model with evaluation metrics (RMSE, MAPE)
and projects revenue for the next 6 months with confidence intervals.
Outputs: outputs/10_revenue_forecast.png and data/revenue_forecast.csv
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"
os.makedirs(OUT_DIR, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / ".matplotlib"))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score

def run_forecast():
    print("=" * 70)
    print("TIME-SERIES REVENUE FORECASTING")
    print("=" * 70)

    # Load cleaned data
    orders_path = DATA_DIR / "fact_orders.csv"
    items_path = DATA_DIR / "fact_order_items.csv"
    orders = pd.read_csv(orders_path, parse_dates=["order_date"])
    items = pd.read_csv(items_path)

    merged = items.merge(orders[["order_id", "order_date"]], on="order_id")
    merged["order_month"] = merged["order_date"].dt.to_period("M").astype(str)

    # Filter to complete calendar months (2023-01 to 2025-12; 2026-01 is a partial 17-day month)
    monthly = merged[merged["order_month"] <= "2025-12"].groupby("order_month")["sales"].sum().reset_index()
    monthly = monthly.sort_values("order_month").reset_index(drop=True)
    monthly["ds"] = pd.to_datetime(monthly["order_month"])
    monthly["time_idx"] = np.arange(len(monthly))
    monthly["month_num"] = monthly["ds"].dt.month

    # Generate cyclical seasonal features (sin/cos of month)
    monthly["sin_month"] = np.sin(2 * np.pi * monthly["month_num"] / 12)
    monthly["cos_month"] = np.cos(2 * np.pi * monthly["month_num"] / 12)

    feature_cols = ["time_idx", "sin_month", "cos_month"]

    # Train / Test split (Hold out last 6 months of 2025 for validation)
    train_size = len(monthly) - 6
    train_df = monthly.iloc[:train_size]
    test_df = monthly.iloc[train_size:]

    model_eval = Ridge(alpha=1.0)
    model_eval.fit(train_df[feature_cols], train_df["sales"])
    test_preds = model_eval.predict(test_df[feature_cols])

    rmse = np.sqrt(mean_squared_error(test_df["sales"], test_preds))
    mape = mean_absolute_percentage_error(test_df["sales"], test_preds)
    r2 = r2_score(test_df["sales"], test_preds)

    print(f"Model Evaluation (Holdout Test on last 6 months):")
    print(f"  RMSE : ${rmse:,.2f}")
    print(f"  MAPE : {mape * 100:.2f}%")
    print(f"  R^2  : {r2:.3f}")

    # Retrain on full dataset for forward forecast
    full_model = Ridge(alpha=1.0)
    full_model.fit(monthly[feature_cols], monthly["sales"])
    monthly["fitted"] = full_model.predict(monthly[feature_cols])
    residuals = monthly["sales"] - monthly["fitted"]
    std_resid = residuals.std()

    # Generate 6 future months
    last_date = monthly["ds"].max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=6, freq="MS")
    future_df = pd.DataFrame({"ds": future_dates})
    future_df["order_month"] = future_df["ds"].dt.to_period("M").astype(str)
    future_df["time_idx"] = np.arange(len(monthly), len(monthly) + len(future_df))
    future_df["month_num"] = future_df["ds"].dt.month
    future_df["sin_month"] = np.sin(2 * np.pi * future_df["month_num"] / 12)
    future_df["cos_month"] = np.cos(2 * np.pi * future_df["month_num"] / 12)

    future_df["forecast"] = full_model.predict(future_df[feature_cols])
    future_df["lower_95"] = future_df["forecast"] - 1.96 * std_resid
    future_df["upper_95"] = future_df["forecast"] + 1.96 * std_resid

    # Export forecast results
    export_df = future_df[["order_month", "forecast", "lower_95", "upper_95"]].copy()
    export_df.columns = ["month", "forecasted_revenue", "lower_95_ci", "upper_95_ci"]
    export_path = DATA_DIR / "revenue_forecast.csv"
    export_df.to_csv(export_path, index=False)
    print(f"\nExported 6-month forecast -> {export_path}")

    # Visualization
    plt.figure(figsize=(12, 6))
    plt.plot(monthly["order_month"], monthly["sales"] / 1000, marker="o", color="#2b5c8f", label="Actual Historical Revenue", linewidth=2)
    plt.plot(monthly["order_month"], monthly["fitted"] / 1000, linestyle="--", color="#6baed6", label="Model Fit", alpha=0.8)

    # Plot future forecast
    plt.plot(future_df["order_month"], future_df["forecast"] / 1000, marker="s", color="#e6550d", linewidth=2.5, label="6-Month Forward Forecast")
    plt.fill_between(future_df["order_month"], future_df["lower_95"] / 1000, future_df["upper_95"] / 1000, color="#fdae6b", alpha=0.35, label="95% Confidence Interval")

    plt.xticks(rotation=90)
    plt.ylabel("Revenue ($ in Thousands)", fontsize=11)
    plt.title("Monthly Revenue: Historical Trend & 6-Month Predictive Forecast", fontsize=13, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper left")
    plt.tight_layout()

    out_chart = OUT_DIR / "10_revenue_forecast.png"
    plt.savefig(out_chart, dpi=120)
    plt.close()
    print(f"Saved forecast visual -> {out_chart}")

if __name__ == "__main__":
    run_forecast()
