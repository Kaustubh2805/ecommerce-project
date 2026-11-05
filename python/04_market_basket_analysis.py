"""
04_market_basket_analysis.py
Performs market basket analysis / association rule mining on multi-item orders.
Identifies strong product co-purchase patterns using Support, Confidence, and Lift.
Outputs: data/market_basket_rules.csv and outputs/11_market_basket_lift.png
"""
import os
from pathlib import Path
from itertools import combinations
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"
os.makedirs(OUT_DIR, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / ".matplotlib"))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def run_market_basket():
    print("=" * 70)
    print("MARKET BASKET & PRODUCT CO-PURCHASE ANALYSIS")
    print("=" * 70)

    items = pd.read_csv(DATA_DIR / "fact_order_items.csv")
    products = pd.read_csv(DATA_DIR / "dim_products.csv")

    df = items.merge(products[["product_id", "product_name", "category", "sub_category"]], on="product_id")

    # Filter to orders with multiple items
    order_counts = df.groupby("order_id")["product_name"].nunique()
    multi_item_orders = order_counts[order_counts >= 2].index
    df_multi = df[df["order_id"].isin(multi_item_orders)]

    total_baskets = len(multi_item_orders)
    print(f"Total multi-item orders analyzed: {total_baskets:,}")

    # Build basket sets (at sub-category level for broad retail strategy & product level for cross-sell)
    baskets = df_multi.groupby("order_id")["sub_category"].apply(lambda s: sorted(set(s))).tolist()

    item_counts = Counter()
    pair_counts = Counter()

    for basket in baskets:
        for item in basket:
            item_counts[item] += 1
        for pair in combinations(basket, 2):
            pair_counts[pair] += 1

    rules = []
    for (item_a, item_b), pair_freq in pair_counts.items():
        if pair_freq < 15:  # Minimum support threshold
            continue

        freq_a = item_counts[item_a]
        freq_b = item_counts[item_b]

        supp_ab = pair_freq / total_baskets
        supp_a = freq_a / total_baskets
        supp_b = freq_b / total_baskets

        conf_a_to_b = supp_ab / supp_a
        conf_b_to_a = supp_ab / supp_b
        lift = supp_ab / (supp_a * supp_b)

        rules.append({
            "item_a": item_a,
            "item_b": item_b,
            "pair_orders": pair_freq,
            "support_pct": round(supp_ab * 100, 2),
            "confidence_a_to_b_pct": round(conf_a_to_b * 100, 2),
            "confidence_b_to_a_pct": round(conf_b_to_a * 100, 2),
            "lift": round(lift, 2),
        })

    rules_df = pd.DataFrame(rules).sort_values("lift", ascending=False).reset_index(drop=True)
    out_csv = DATA_DIR / "market_basket_rules.csv"
    rules_df.to_csv(out_csv, index=False)
    print(f"\nTop Co-Purchase Rules (Sub-Category Level):")
    print(rules_df.head(10).to_string(index=False))
    print(f"\nSaved rules -> {out_csv}")

    # Visualizing Top 10 Cross-Sell Associations by Lift
    top_rules = rules_df.head(10).copy()
    top_rules["pair_label"] = top_rules["item_a"] + "  +  " + top_rules["item_b"]

    plt.figure(figsize=(10, 5.5))
    colors = plt.cm.viridis(np.linspace(0.3, 0.85, len(top_rules)))
    bars = plt.barh(top_rules["pair_label"][::-1], top_rules["lift"][::-1], color=colors)

    plt.axvline(x=1.0, color="#d95f02", linestyle="--", linewidth=1.5, label="Baseline (Lift = 1.0, Independent)")
    plt.xlabel("Lift Ratio (Values > 1.0 indicate positive cross-sell affinity)", fontsize=11)
    plt.title("Top 10 Product Affinity Pairs by Lift", fontsize=13, fontweight="bold")
    plt.legend(loc="lower right")

    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.02, bar.get_y() + bar.get_height()/2, f"{width:.2f}x",
                 va="center", ha="left", fontsize=9, fontweight="bold")

    plt.tight_layout()
    out_chart = OUT_DIR / "11_market_basket_lift.png"
    plt.savefig(out_chart, dpi=120)
    plt.close()
    print(f"Saved association chart -> {out_chart}")

if __name__ == "__main__":
    run_market_basket()
