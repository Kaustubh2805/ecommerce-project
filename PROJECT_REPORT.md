# Project Report
## E-Commerce Sales & Customer Analysis — SQL + Python + Power BI

**Type:** End-to-end data analytics portfolio project
**Stack:** SQL (SQLite/PostgreSQL-compatible) · Python (pandas, scikit-learn, matplotlib/seaborn) · Power BI
**Author's role:** Data Analyst / Analytics Engineer

---

## 1. Executive Summary

This project builds a complete analytics pipeline around e-commerce transactional
data — from raw relational tables through SQL-based analysis, Python-based
exploratory analysis and customer segmentation, and finally a Power BI
dashboard layer. It is designed to demonstrate the full skill set expected of
a data/business analyst: **data modeling, SQL querying, statistical/ML
analysis in Python, and BI dashboard design** — using one coherent dataset and
narrative rather than three disconnected exercises.

The deliverable is organized so each layer builds on the last:

```
Raw Data → SQL (schema + analysis) → Python (clean, explore, segment) → Power BI (model + dashboard)
```

---

## 2. Objectives

| # | Objective | Why it matters |
|---|---|---|
| 1 | Design a normalized relational schema for e-commerce data | Shows data modeling competency, not just flat-file analysis |
| 2 | Answer core business questions in SQL | SQL is the most commonly tested/used skill in analyst interviews and day-to-day work |
| 3 | Clean and validate data programmatically | Real data is never clean; demonstrating QA checks builds credibility |
| 4 | Segment customers (RFM + clustering) | Turns raw transactions into an actionable customer strategy |
| 5 | Measure retention via cohort analysis | A retention lens is what separates "reporting" from "analysis" |
| 6 | Build a BI layer with a proper star schema and DAX | Shows the analyst can hand off to/operate in a self-service BI tool, not just notebooks |
| 7 | Package everything as a reproducible, documented, GitHub-ready repo | Portfolio value — a recruiter/hiring manager can run it themselves |

---

## 3. Business Questions This Project Answers

Grouped the way a stakeholder would ask them:

**Sales performance**
- How is revenue and profit trending month over month, and year over year?
- Which regions and customer segments are most profitable?
- Does discounting actually grow revenue, or does it just erode margin?
- Which shipping modes are used most, and how fast is fulfillment?

**Product performance**
- What are the top-selling and most profitable products/categories?
- Are there products that sell well but lose money (negative/thin margin)?
- Which categories have the highest return rates?

**Customer analytics**
- Who are our highest-value customers (RFM / lifetime value)?
- What natural customer segments exist in the data (data-driven clustering, not just rules)?
- What fraction of customers come back and buy again?
- How does retention decay over time after a customer's first purchase (cohort analysis)?

---

## 4. Tech Stack & Why Each Tool Was Chosen

| Layer | Tool | Role |
|---|---|---|
| Data storage / querying | **SQLite** (portable to PostgreSQL/MySQL with minor syntax changes) | Relational modeling, indexed joins, window-function analysis |
| Data generation, cleaning, stats & ML | **Python** — `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn` | Data QA, EDA, RFM scoring, K-Means clustering, cohort math, charting |
| Dashboarding / BI | **Power BI** (Desktop) | Star-schema modeling, DAX time-intelligence, interactive stakeholder-facing dashboard |
| Documentation | **Markdown** | Version-control-friendly, renders natively on GitHub |

---

## 5. Data Architecture

### 5.1 Source Note
No live dataset was pulled from the internet for this build (no network
access in the build environment). Instead, a **synthetic dataset was
generated to be schema-identical to the well-known Superstore/Olist-style
e-commerce datasets** — same kind of fields, realistic seasonality,
discounting behavior, and a Pareto-distributed (few big spenders, many small
ones) customer base, matching real retail data patterns. Every script in this
project runs unchanged against the real Superstore or Olist CSVs if you
substitute them in.

### 5.2 Entity-Relationship Model

```
dim_customers  ───┐
                   │
dim_products   ───┼──► fact_orders ──► fact_order_items
                   │         │
                   │         └──► fact_returns
                   │
              (customer_segments, derived by Python — RFM + cluster labels)
```

| Table | Grain | Key Columns |
|---|---|---|
| `dim_customers` | 1 row per customer | customer_id (PK), segment, region, signup_date |
| `dim_products` | 1 row per product | product_id (PK), category, sub_category, unit_price, unit_cost |
| `fact_orders` | 1 row per order | order_id (PK), customer_id (FK), order_date, ship_mode |
| `fact_order_items` | 1 row per order line item | order_item_id (PK), order_id (FK), product_id (FK), quantity, discount, sales, profit |
| `fact_returns` | 1 row per returned order | order_id (FK), return_date, return_reason |
| `customer_segments` (derived) | 1 row per customer | RFM scores, rfm_segment, K-Means cluster_name |

### 5.3 Scale
~800 customers · ~216 products · 6,500 orders · ~12,900 order line items ·
3 years of daily transaction history (2023–2025) — large enough to make
trends, seasonality, and clustering meaningful, small enough to run instantly
on a laptop.

---

## 6. How the Project Should Be Built — Step by Step

### Phase 1 — Data Foundation
1. **Design the schema first**, on paper or in a diagram tool, before writing a single query. Decide grain of each table (this project intentionally normalizes into `fact_orders` + `fact_order_items` rather than one flat Superstore-style table, so it exercises real join logic).
2. **Generate or source the data.** If using a real dataset (Olist, Kaggle Superstore), download and inspect column types before loading. If generating synthetically, bake in realism: seasonality, an unequal (power-law) distribution of customer spend, a plausible return rate, varied discount levels — flat/random synthetic data produces boring, uninformative analysis.
3. **Load into a relational database** (SQLite for portability, or PostgreSQL/MySQL for a closer-to-production feel). Enforce primary/foreign keys and add indexes on join and filter columns (`customer_id`, `order_date`, `product_id`).

### Phase 2 — SQL Analysis Layer
4. Write the **schema DDL** (`CREATE TABLE`, keys, indexes) as its own versioned file — this is what a reviewer checks first to judge data-modeling skill.
5. Write **analysis queries in layers of increasing complexity**:
   - Simple aggregates (revenue by month, by region)
   - Window functions (YoY growth via `LAG`, ranking via `RANK`, quantile scoring via `NTILE`)
   - CTEs chained together for multi-step logic (RFM scoring, cohort index calculation)
   - Each query should answer one specific business question from Section 3 — don't write throwaway queries with no stated purpose.
6. **Validate every query executes cleanly** against the actual loaded data before calling it done — a query that "looks right" but errors on real data undermines the whole project.

### Phase 3 — Python Analysis Layer
7. **Data quality pass first, always.** Before any chart or model: check nulls, duplicates, referential integrity (orphan rows), and impossible values (negative sales, ship date before order date). Print/report the results — this is what shows rigor to a reviewer.
8. **Build one denormalized "analysis-ready" table** by joining the fact/dim tables — most EDA and charting is easier on a flat table than repeatedly re-joining.
9. **Exploratory Data Analysis (EDA):** compute headline KPIs (revenue, profit, margin, AOV, return rate), then visualize:
   - Trend over time (revenue/profit by month)
   - Category × region breakdown (heatmap)
   - Top products
   - Segment comparison
   - Discount-vs-margin relationship (this is usually the single most "insightful" chart in an e-commerce project — it directly informs pricing strategy)
10. **Customer segmentation, two complementary methods:**
    - **RFM (Recency, Frequency, Monetary) scoring** — rule-based, interpretable, industry-standard. Score each dimension into quintiles, then map score combinations to named tiers (Champions, Loyal, At Risk, Hibernating, etc.).
    - **K-Means clustering** on scaled R/F/M values — a data-driven cross-check on the rule-based segments. Use the elbow method to justify the chosen number of clusters (k). Name clusters by their monetary rank (High-Value, Mid-Value, Low-Value, Dormant) so they're interpretable to a non-technical stakeholder.
11. **Cohort retention analysis:** group customers by the month of their first purchase, then track what % of each cohort is still active in each subsequent month. Visualize as a heatmap — this is the clearest way to communicate retention decay to a stakeholder.
12. **Export segment and cohort outputs to CSV** — these become inputs to the Power BI layer, so Python's "smart" analysis (clustering, RFM) is visible inside the BI tool too, not siloed in a notebook.

### Phase 4 — Power BI Layer
13. **Re-shape data into a star schema** before importing to Power BI: one central fact table (`fact_sales`, grain = order line item) surrounded by dimension tables (`dim_customers`, `dim_products`, `dim_date`, `dim_customer_segments`, `dim_returns`). Avoid importing a single wide flat table — a star schema is what makes DAX time-intelligence functions and cross-filtering work correctly and keeps the model fast.
14. **Build a dedicated `dim_date` table** and mark it as the official Date Table in Power BI — required for `SAMEPERIODLASTYEAR`, `TOTALMTD`, and other time-intelligence DAX functions to work correctly.
15. **Define relationships explicitly** in Model view (all fact-to-dimension relationships as many-to-one, single-direction filtering, unless a specific visual requires bi-directional).
16. **Write DAX measures, not calculated columns, for anything aggregatable** (Total Revenue, Profit Margin %, YoY Growth, Repeat Purchase Rate, CLV) — measures are dynamic to filter context, calculated columns are not, and DAX measures are what's expected in professional Power BI work.
17. **Design pages around audiences, not tables:** an Executive Overview (KPI cards + trend), a Sales Analysis page (category/region breakdowns), a Product Performance page, and a Customer Analytics page (RFM/cluster visuals, cohort heatmap). Each page should answer a specific subset of the business questions in Section 3, not just dump every visual on one canvas.

### Phase 5 — Packaging & Documentation
18. Write a **README** that lets a stranger reproduce the entire project from scratch: setup, run order, and headline findings.
19. Organize files into clear folders (`data/`, `sql/`, `python/`, `powerbi/`, `outputs/`) — folder structure is itself a signal of analytical maturity.
20. State data provenance clearly (synthetic vs. real) — never let a reviewer discover synthetic data on their own; disclose it upfront, and explain why it's schema-compatible with real data so the analytical work still counts.

---

## 7. Methodology Notes on the Analytical Techniques Used

**RFM Segmentation**
Recency, Frequency, and Monetary value are each scored 1–5 via quintile
(`NTILE`/`qcut`) binning, then combined into named segments. This is the
industry-standard, boardroom-friendly way to segment customers because it's
transparent — a marketing stakeholder can understand *why* a customer landed
in "At Risk" without needing to understand the underlying math.

**K-Means Clustering**
Run as a cross-check against the rule-based RFM tiers. Recency, Frequency,
and Monetary are standardized (`StandardScaler`) before clustering, since
K-Means is distance-based and the three raw features are on very different
scales (days vs. order count vs. dollars). The elbow method (plotting
inertia across k=2..8) is used to choose the number of clusters rather than
picking an arbitrary k. In this project, k=4 was chosen at the elbow point.

**Cohort Retention Analysis**
Customers are grouped into a "cohort" by the calendar month of their first
purchase. For every subsequent month, the % of that cohort still purchasing
is calculated, producing a triangular retention matrix — the standard SaaS/
e-commerce retention visualization.

**Why both a rule-based and an ML-based segmentation?**
Presenting only RFM risks looking like a templated exercise; presenting only
K-Means risks being a black box a stakeholder can't act on. Showing both, and
that they broadly agree, demonstrates both statistical/ML capability and
business communication judgment — knowing when a simpler, explainable method
is the right deliverable.

---

## 8. Key Findings (from this project's dataset)

| Metric | Value |
|---|---|
| Total Revenue | $15.2M |
| Total Profit | $1.54M |
| Profit Margin | 10.1% |
| Total Orders | 6,500 |
| Unique Customers | 764 |
| Average Order Value | $2,338 |
| Return Rate | 5.5% |

- Revenue is strongly seasonal, spiking ~2.2x in November–December.
- Profit margin erodes sharply once discounts exceed ~20% — a clear pricing-policy signal.
- Customer value is Pareto-distributed: a small "High-Value" cluster (~7% of customers) drives a disproportionate share of total revenue, confirmed independently by both RFM scoring and K-Means clustering.
- Retention drops fastest in the first month after a customer's initial purchase, then stabilizes — the highest-leverage point for a retention/lifecycle-marketing intervention is month 0→1.

---

## 9. Skills Demonstrated (for resume/portfolio framing)

- **SQL:** relational schema design, primary/foreign keys, indexing strategy, window functions (`LAG`, `NTILE`, `RANK`), multi-step CTEs, date arithmetic, RFM scoring in pure SQL.
- **Python:** data validation/QA, `pandas` data wrangling, `scikit-learn` unsupervised learning (K-Means + elbow method), statistical segmentation (RFM), cohort-retention matrix construction, `matplotlib`/`seaborn` visualization design.
- **Power BI / DAX:** star-schema data modeling, date-dimension design, DAX time-intelligence, calculated measures for CLV/repeat-rate/margin, dashboard/page design for distinct stakeholder audiences.
- **Analytics craft:** translating raw transactional data into business questions and back into stakeholder-usable answers; documentation and reproducibility.

---

## 10. Limitations & Honest Caveats

- The underlying data is synthetic, not a real company's transactions — trends and segment sizes are illustrative, not a real business's actuals.
- Return reasons, discount policy, and shipping SLAs are modeled with simplifying assumptions and won't capture every real-world edge case (e.g., partial-order returns, multi-warehouse logistics).
- K-Means with k=4 is one reasonable choice at the elbow; a different business context might justify a different k or a different clustering algorithm (e.g., DBSCAN for non-spherical segments).

---

## 11. Suggested Extensions

- **Forecasting:** add a time-series model (Prophet or ARIMA) on the monthly revenue series to project the next 3–6 months.
- **Market-basket analysis:** association-rule mining (Apriori/FP-Growth) on `fact_order_items` to find frequently co-purchased products.
- **A/B test simulation:** simulate a discount-policy change and measure the modeled revenue/margin impact.
- **Live deployment:** publish the Power BI report to the Power BI Service and embed a dashboard screenshot/GIF in the README for portfolio presentation.
- **Real data swap-in:** replace the synthetic CSVs with the real Kaggle Olist or Superstore dataset (same column contract) to turn this into a live-data portfolio piece.

---

## 12. Repository Structure Reference

```
ecommerce_project/
├── data/                         # Raw relational CSVs, derived tables & SQLite DB
├── sql/                          # DDL table schemas & 14 business queries
├── notebooks/                    # Interactive Jupyter portfolio walkthrough
├── python/                       # Ingestion, EDA, ML, forecasting & Power BI ETL
├── tests/                        # Automated data quality & integrity test suite
├── outputs/                      # 11 high-resolution analytical charts
├── powerbi/                      # Star-schema exports + DAX/build guide
├── run_pipeline.py               # Master end-to-end pipeline orchestrator
├── README.md                     # Setup, reproduction guide & visual gallery
├── PROJECT_REPORT.md             # This document
└── requirements.txt
```

---

*This report is intended to accompany the project codebase as documentation of scope, methodology, and rationale — suitable for inclusion in a GitHub repository or as a supporting document in a portfolio/interview walkthrough.*
