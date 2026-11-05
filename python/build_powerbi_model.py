"""
build_powerbi_model.py
Transforms relational tables into a clean star schema tailored for Power BI Desktop.
Generates:
  - fact_sales.csv (denormalized line items with order headers)
  - dim_date.csv (calendar dimension for time intelligence)
  - dim_customers.csv, dim_products.csv, dim_returns.csv
  - dim_customer_segments.csv (synchronized RFM + K-Means cluster outputs)
  - cohort_retention.csv
Saves all files to powerbi/data_model/
"""
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PBI_DIR = BASE_DIR / "powerbi" / "data_model"
PBI_DIR.mkdir(parents=True, exist_ok=True)

def build_powerbi_model():
    print("=" * 70)
    print("BUILDING POWER BI STAR-SCHEMA DATA MODEL")
    print(f"Target Directory: {PBI_DIR}")
    print("=" * 70)

    # 1. Load source tables
    orders = pd.read_csv(DATA_DIR / "fact_orders.csv", parse_dates=["order_date", "ship_date"])
    items = pd.read_csv(DATA_DIR / "fact_order_items.csv")
    customers = pd.read_csv(DATA_DIR / "dim_customers.csv")
    products = pd.read_csv(DATA_DIR / "dim_products.csv")
    returns = pd.read_csv(DATA_DIR / "fact_returns.csv")

    # 2. Build fact_sales (grain = order line item)
    fact_sales = items.merge(
        orders[["order_id", "customer_id", "order_date", "ship_date", "ship_mode"]],
        on="order_id",
        how="left"
    )
    fact_sales["order_date"] = fact_sales["order_date"].dt.strftime("%Y-%m-%d")
    fact_sales["ship_date"] = fact_sales["ship_date"].dt.strftime("%Y-%m-%d")

    sales_cols = [
        "order_item_id", "order_id", "product_id", "quantity",
        "unit_price", "discount", "sales", "profit",
        "customer_id", "order_date", "ship_date", "ship_mode"
    ]
    fact_sales = fact_sales[sales_cols]
    fact_sales.to_csv(PBI_DIR / "fact_sales.csv", index=False)
    print(f"  Generated fact_sales.csv: {len(fact_sales):,d} rows")

    # 3. Generate dim_date (comprehensive date dimension)
    min_date = orders["order_date"].min()
    max_date = orders["ship_date"].max() + pd.DateOffset(days=30)
    date_range = pd.date_range(start=min_date, end=max_date, freq="D")

    dim_date = pd.DataFrame({"date": date_range})
    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.strftime("%B")
    dim_date["quarter"] = "Q" + dim_date["date"].dt.quarter.astype(str)
    dim_date["day_of_week"] = dim_date["date"].dt.day_name()
    dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5
    dim_date["date"] = dim_date["date"].dt.strftime("%Y-%m-%d")

    dim_date.to_csv(PBI_DIR / "dim_date.csv", index=False)
    print(f"  Generated dim_date.csv: {len(dim_date):,d} days ({min_date.date()} to {max_date.date()})")

    # 4. Copy core dimensions
    customers.to_csv(PBI_DIR / "dim_customers.csv", index=False)
    products.to_csv(PBI_DIR / "dim_products.csv", index=False)
    returns.to_csv(PBI_DIR / "dim_returns.csv", index=False)
    print("  Copied dim_customers.csv, dim_products.csv, dim_returns.csv")

    # 5. Synchronize Python segmentation outputs if available
    seg_path = DATA_DIR / "customer_segments.csv"
    if seg_path.exists():
        seg_df = pd.read_csv(seg_path)
        # Select customer segmentation dimension columns
        seg_cols = [c for c in ["customer_id", "recency", "frequency", "monetary",
                                "r_score", "f_score", "m_score", "rfm_score",
                                "rfm_segment", "cluster", "cluster_name"] if c in seg_df.columns]
        seg_df[seg_cols].to_csv(PBI_DIR / "dim_customer_segments.csv", index=False)
        print(f"  Synchronized dim_customer_segments.csv: {len(seg_df):,d} customers")

    cohort_path = DATA_DIR / "cohort_retention.csv"
    if cohort_path.exists():
        shutil.copy(cohort_path, PBI_DIR / "cohort_retention.csv")
        print("  Synchronized cohort_retention.csv")

    print("\nPower BI star-schema model build complete and synchronized.")

if __name__ == "__main__":
    build_powerbi_model()
