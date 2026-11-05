"""
01_data_cleaning_eda.py
Load raw CSVs, validate/clean, and run exploratory data analysis.
Outputs: cleaned CSVs (data/clean/), summary stats printed, charts saved to outputs/.
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
import seaborn as sns

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.dpi"] = 110

# ----------------------------------------------------------------------------
# Load
# ----------------------------------------------------------------------------
customers = pd.read_csv(f"{DATA_DIR}/dim_customers.csv", parse_dates=["signup_date"])
products = pd.read_csv(f"{DATA_DIR}/dim_products.csv")
orders = pd.read_csv(f"{DATA_DIR}/fact_orders.csv", parse_dates=["order_date", "ship_date"])
items = pd.read_csv(f"{DATA_DIR}/fact_order_items.csv")
returns = pd.read_csv(f"{DATA_DIR}/fact_returns.csv", parse_dates=["return_date"])

print("=" * 70)
print("DATA QUALITY CHECK")
print("=" * 70)
for name, df in [("customers", customers), ("products", products),
                  ("orders", orders), ("items", items), ("returns", returns)]:
    nulls = df.isna().sum().sum()
    dupes = df.duplicated().sum()
    print(f"{name:12s} rows={len(df):6d}  nulls={nulls:4d}  dupes={dupes:3d}")

# Basic integrity checks (referential)
orphan_items = items[~items.order_id.isin(orders.order_id)]
orphan_orders = orders[~orders.customer_id.isin(customers.customer_id)]
print(f"\nOrphan order_items (no parent order): {len(orphan_items)}")
print(f"Orphan orders (no parent customer):   {len(orphan_orders)}")

# Negative / invalid value checks
neg_sales = items[items.sales < 0]
neg_qty = items[items.quantity <= 0]
ship_before_order = orders[orders.ship_date < orders.order_date]
print(f"Negative sales rows: {len(neg_sales)}")
print(f"Non-positive quantity rows: {len(neg_qty)}")
print(f"Ship date before order date: {len(ship_before_order)}")

# ----------------------------------------------------------------------------
# Build an analysis-ready denormalized table
# ----------------------------------------------------------------------------
df = (items
      .merge(orders, on="order_id", how="left")
      .merge(customers, on="customer_id", how="left")
      .merge(products, on="product_id", how="left"))
df["order_date"] = pd.to_datetime(df["order_date"])
df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
df["is_returned"] = df["order_id"].isin(returns.order_id)

clean_dir = f"{DATA_DIR}/clean"
os.makedirs(clean_dir, exist_ok=True)
df.to_csv(f"{clean_dir}/analysis_ready.csv", index=False)
print(f"\nSaved denormalized analysis table: {len(df)} rows -> data/clean/analysis_ready.csv")

# ----------------------------------------------------------------------------
# EDA: headline KPIs
# ----------------------------------------------------------------------------
total_revenue = df.sales.sum()
total_profit = df.profit.sum()
total_orders = df.order_id.nunique()
total_customers = df.customer_id.nunique()
aov = total_revenue / total_orders
margin = 100 * total_profit / total_revenue

print("\n" + "=" * 70)
print("HEADLINE KPIs")
print("=" * 70)
print(f"Total Revenue      : ${total_revenue:,.2f}")
print(f"Total Profit       : ${total_profit:,.2f}")
print(f"Profit Margin      : {margin:.1f}%")
print(f"Total Orders       : {total_orders:,}")
print(f"Unique Customers   : {total_customers:,}")
print(f"Avg Order Value    : ${aov:,.2f}")
print(f"Return Rate        : {100*returns.order_id.nunique()/total_orders:.2f}%")

# ----------------------------------------------------------------------------
# Chart 1: Monthly revenue & profit trend
# ----------------------------------------------------------------------------
monthly = df.groupby("order_month").agg(revenue=("sales", "sum"), profit=("profit", "sum")).reset_index()
fig, ax1 = plt.subplots(figsize=(12, 5))
ax1.bar(monthly.order_month, monthly.revenue, color="#4C72B0", alpha=0.85, label="Revenue")
ax1.set_ylabel("Revenue ($)")
ax1.tick_params(axis='x', rotation=90)
ax2 = ax1.twinx()
ax2.plot(monthly.order_month, monthly.profit, color="#DD8452", marker="o", linewidth=2, label="Profit")
ax2.set_ylabel("Profit ($)")
fig.suptitle("Monthly Revenue & Profit Trend", fontsize=13, fontweight="bold")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2, labels1+labels2, loc="upper left")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/01_monthly_revenue_profit.png")
plt.close()

# ----------------------------------------------------------------------------
# Chart 2: Revenue by category & region (heatmap)
# ----------------------------------------------------------------------------
pivot = df.pivot_table(index="category", columns="region", values="sales", aggfunc="sum")
plt.figure(figsize=(8, 4.5))
sns.heatmap(pivot, annot=True, fmt=",.0f", cmap="Blues", cbar_kws={"label": "Revenue ($)"})
plt.title("Revenue by Category x Region", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/02_category_region_heatmap.png")
plt.close()

# ----------------------------------------------------------------------------
# Chart 3: Top 10 products by revenue
# ----------------------------------------------------------------------------
top_products = df.groupby("product_name").sales.sum().sort_values(ascending=False).head(10)
plt.figure(figsize=(9, 5))
sns.barplot(x=top_products.values, y=top_products.index, color="#55A868")
plt.xlabel("Revenue ($)")
plt.title("Top 10 Products by Revenue", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/03_top_products.png")
plt.close()

# ----------------------------------------------------------------------------
# Chart 4: Customer segment distribution & AOV
# ----------------------------------------------------------------------------
seg = df.groupby("segment").agg(revenue=("sales", "sum"),
                                 orders=("order_id", "nunique")).reset_index()
seg["aov"] = seg.revenue / seg.orders
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
sns.barplot(data=seg, x="segment", y="revenue", ax=axes[0], color="#4C72B0")
axes[0].set_title("Revenue by Segment")
sns.barplot(data=seg, x="segment", y="aov", ax=axes[1], color="#C44E52")
axes[1].set_title("Avg Order Value by Segment")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/04_segment_analysis.png")
plt.close()

# ----------------------------------------------------------------------------
# Chart 5: Discount vs profit margin
# ----------------------------------------------------------------------------
items_tmp = items.copy()
items_tmp["discount_band"] = pd.cut(items_tmp.discount,
    bins=[-0.01, 0, 0.10, 0.20, 1.0], labels=["0%", "1-10%", "11-20%", "21%+"])
band = items_tmp.groupby("discount_band", observed=True).agg(
    revenue=("sales", "sum"), profit=("profit", "sum")).reset_index()
band["margin_pct"] = 100 * band.profit / band.revenue
plt.figure(figsize=(7, 4.5))
sns.barplot(data=band, x="discount_band", y="margin_pct", color="#8172B2")
plt.ylabel("Profit Margin (%)")
plt.title("Profit Margin Erosion by Discount Band", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/05_discount_margin.png")
plt.close()

print(f"\nSaved 5 charts to {OUT_DIR}/")
print("EDA complete.")
