"""
02_customer_segmentation.py
RFM analysis + K-Means clustering for customer segmentation, plus cohort
retention analysis. Outputs a customer_segments.csv for Power BI and charts.
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
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 110

orders = pd.read_csv(f"{DATA_DIR}/fact_orders.csv", parse_dates=["order_date"])
items = pd.read_csv(f"{DATA_DIR}/fact_order_items.csv")
customers = pd.read_csv(f"{DATA_DIR}/dim_customers.csv")

order_rev = items.groupby("order_id").sales.sum().reset_index()
oc = orders.merge(order_rev, on="order_id")

# ----------------------------------------------------------------------------
# RFM calculation
# ----------------------------------------------------------------------------
ref_date = oc.order_date.max() + pd.Timedelta(days=1)
rfm = oc.groupby("customer_id").agg(
    last_order=("order_date", "max"),
    frequency=("order_id", "nunique"),
    monetary=("sales", "sum"),
).reset_index()
rfm["recency"] = (ref_date - rfm.last_order).dt.days
rfm = rfm[["customer_id", "recency", "frequency", "monetary"]]

# RFM quintile scores (1-5, 5 = best)
rfm["r_score"] = pd.qcut(rfm.recency, 5, labels=[5,4,3,2,1]).astype(int)
rfm["f_score"] = pd.qcut(rfm.frequency.rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
rfm["m_score"] = pd.qcut(rfm.monetary, 5, labels=[1,2,3,4,5]).astype(int)
rfm["rfm_score"] = rfm.r_score.astype(str) + rfm.f_score.astype(str) + rfm.m_score.astype(str)

def rfm_tier(row):
    if row.r_score >= 4 and row.f_score >= 4:
        return "Champions"
    if row.r_score >= 3 and row.f_score >= 3:
        return "Loyal Customers"
    if row.r_score >= 4 and row.f_score <= 2:
        return "New / Promising"
    if row.r_score <= 2 and row.f_score >= 4:
        return "At Risk"
    if row.r_score <= 2 and row.f_score <= 2:
        return "Hibernating / Lost"
    return "Needs Attention"

rfm["rfm_segment"] = rfm.apply(rfm_tier, axis=1)

print("RFM Segment distribution:")
print(rfm.rfm_segment.value_counts())

# ----------------------------------------------------------------------------
# K-Means clustering on scaled R, F, M (data-driven alternative to rule-based tiers)
# ----------------------------------------------------------------------------
X = rfm[["recency", "frequency", "monetary"]].copy()
X_scaled = StandardScaler().fit_transform(X)

# Elbow method
inertias = []
K_range = range(2, 9)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X_scaled)
    inertias.append(km.inertia_)

plt.figure(figsize=(6, 4))
plt.plot(list(K_range), inertias, marker="o")
plt.xlabel("k (clusters)")
plt.ylabel("Inertia")
plt.title("Elbow Method for Optimal k")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/06_kmeans_elbow.png")
plt.close()

K_FINAL = 4
km_final = KMeans(n_clusters=K_FINAL, random_state=42, n_init=10).fit(X_scaled)
rfm["cluster"] = km_final.labels_

cluster_profile = rfm.groupby("cluster").agg(
    customers=("customer_id", "count"),
    avg_recency=("recency", "mean"),
    avg_frequency=("frequency", "mean"),
    avg_monetary=("monetary", "mean"),
).round(1).sort_values("avg_monetary", ascending=False)
print("\nK-Means cluster profile:")
print(cluster_profile)

# Name clusters by monetary rank for readability
rank_order = cluster_profile.index.tolist()
cluster_names = {}
labels_ranked = ["High-Value", "Mid-Value", "Low-Value", "Dormant"]
for i, cl in enumerate(rank_order):
    cluster_names[cl] = labels_ranked[i] if i < len(labels_ranked) else f"Cluster {cl}"
rfm["cluster_name"] = rfm.cluster.map(cluster_names)

# ----------------------------------------------------------------------------
# Merge with customer attributes and save for Power BI
# ----------------------------------------------------------------------------
out = rfm.merge(customers[["customer_id","customer_name","segment","region","city","state"]],
                 on="customer_id", how="left")
out.to_csv(f"{DATA_DIR}/customer_segments.csv", index=False)
print(f"\nSaved customer_segments.csv ({len(out)} customers)")

# Chart: cluster scatter (frequency vs monetary, colored by cluster)
plt.figure(figsize=(8, 5.5))
sns.scatterplot(data=rfm, x="frequency", y="monetary", hue="cluster_name",
                 palette="deep", s=45, alpha=0.75)
plt.title("Customer Clusters: Frequency vs Monetary Value", fontsize=13, fontweight="bold")
plt.xlabel("Order Frequency"); plt.ylabel("Total Spend ($)")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/07_customer_clusters.png")
plt.close()

# Chart: RFM segment counts
plt.figure(figsize=(8, 4.5))
order_ = rfm.rfm_segment.value_counts().index
sns.countplot(data=rfm, y="rfm_segment", order=order_, color="#4C72B0")
plt.title("Customers by RFM Segment", fontsize=13, fontweight="bold")
plt.xlabel("Customers")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/08_rfm_segments.png")
plt.close()

# ----------------------------------------------------------------------------
# Cohort retention analysis
# ----------------------------------------------------------------------------
first_purchase = oc.groupby("customer_id").order_date.min().dt.to_period("M").rename("cohort_month")
oc2 = oc.join(first_purchase, on="customer_id")
oc2["order_month"] = oc2.order_date.dt.to_period("M")
oc2["month_index"] = (oc2.order_month - oc2.cohort_month).apply(lambda x: x.n)

cohort_counts = oc2.groupby(["cohort_month","month_index"]).customer_id.nunique().reset_index()
cohort_pivot = cohort_counts.pivot(index="cohort_month", columns="month_index", values="customer_id")
cohort_size = cohort_pivot[0]
retention = cohort_pivot.divide(cohort_size, axis=0).round(3)

retention.to_csv(f"{DATA_DIR}/cohort_retention.csv")

plt.figure(figsize=(12, 7))
sns.heatmap(retention.iloc[:, :12] * 100, annot=True, fmt=".0f", cmap="YlGnBu",
            cbar_kws={"label": "Retention %"})
plt.title("Monthly Cohort Retention (%)", fontsize=13, fontweight="bold")
plt.xlabel("Months Since First Purchase"); plt.ylabel("Cohort Month")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/09_cohort_retention.png")
plt.close()

print("\nSaved cohort_retention.csv and retention heatmap.")
print("Segmentation & cohort analysis complete.")
