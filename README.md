# E-Commerce Sales & Customer Analysis
**SQL · Python · Power BI — End-to-End Data Analytics Project**

A complete analytics pipeline on e-commerce order data: relational SQL modeling
and analysis, Python EDA + customer segmentation (RFM & K-Means clustering) +
cohort retention, and a Power BI dashboard layer with a star-schema data model
and DAX measures.

> **Dataset note:** This project uses a **synthetic dataset generated to match
> the structure of the well-known "Superstore" e-commerce dataset**, normalized
> into a proper relational schema (customers, products, orders, order items,
> returns) with realistic seasonality, discounting, returns, and customer
> purchase-frequency patterns (Pareto-distributed, like real retail data).
> Every SQL query, Python script, and Power BI model here is schema-compatible
> with the real Superstore or Olist datasets — swap `data/*.csv` for the real
> files and everything downstream still runs.

## 📁 Project Structure

```
ecommerce_project/
├── data/
│   ├── dim_customers.csv        # 800 customers
│   ├── dim_products.csv         # 216 products across 3 categories
│   ├── fact_orders.csv          # 6,500 orders (2023–2025)
│   ├── fact_order_items.csv     # 12,920 line items
│   ├── fact_returns.csv         # ~5.5% return rate
│   ├── customer_segments.csv    # RFM + K-Means output (from Python)
│   ├── cohort_retention.csv     # Cohort retention matrix (from Python)
│   ├── clean/analysis_ready.csv # Denormalized table for analysis
│   └── ecommerce.db             # SQLite database (all tables loaded)
├── sql/
│   ├── 01_schema.sql            # Table definitions, keys, indexes
│   └── 02_analysis_queries.sql  # 14 analysis queries (sales, product, RFM, cohort)
├── python/
│   ├── generate_data.py         # Synthetic data generator
│   ├── run_sql_analysis.py      # Automated runner for all 14 SQL analysis queries
│   ├── 01_data_cleaning_eda.py  # Data quality checks + EDA + 5 charts
│   └── 02_customer_segmentation.py # RFM, K-Means clustering, cohort retention
├── outputs/                     # 9 generated PNG charts
├── powerbi/
│   ├── data_model/              # Star-schema CSVs ready to import
│   └── POWERBI_GUIDE.md         # Relationships, DAX measures, page layout
└── requirements.txt
```

## 🔧 How to Reproduce

```bash
# 1. Set up environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. (Optional) Re-generate the synthetic dataset
python python/generate_data.py

# 3. Run SQL analysis (executes all 14 queries against data/ecommerce.db)
python python/run_sql_analysis.py

# 4. Run Python EDA + customer segmentation & cohort retention
python python/01_data_cleaning_eda.py
python python/02_customer_segmentation.py

# 5. Power BI
# Open Power BI Desktop → Get Data → Text/CSV → import everything in powerbi/data_model/
# Follow powerbi/POWERBI_GUIDE.md for relationships and DAX measures
```

## 📊 Key Findings (from this synthetic run)

| Metric | Value |
|---|---|
| Total Revenue | $15.2M |
| Total Profit | $1.54M |
| Profit Margin | 10.1% |
| Total Orders | 6,500 |
| Unique Customers | 764 |
| Avg Order Value | $2,338 |
| Return Rate | 5.5% |

- **Seasonality:** Revenue spikes ~2.2x in Nov–Dec (holiday effect built into the model).
- **Discounting hurts margin fast:** profit margin drops sharply once discounts exceed ~20% (see `outputs/05_discount_margin.png`).
- **Customer concentration:** a small "Champions" / "High-Value" cluster (top ~7% of customers) drives a disproportionate share of revenue — classic Pareto pattern, confirmed by both the RFM rule-based segmentation and the independent K-Means clustering.
- **Retention decays fast after month 1** then stabilizes — visible in the cohort retention heatmap (`outputs/09_cohort_retention.png`).

## 🧠 Techniques Demonstrated

- **SQL:** window functions (`LAG`, `NTILE`, `RANK`), CTEs, self-referential date math, cohort-index calculation, RFM scoring in pure SQL.
- **Python:** data quality/referential-integrity checks, denormalization for analysis, RFM segmentation, K-Means clustering with the elbow method, cohort retention matrix construction, multi-chart EDA with `matplotlib`/`seaborn`.
- **Power BI:** star-schema design, a dedicated date dimension, DAX time-intelligence (`SAMEPERIODLASTYEAR`, `TOTALMTD`), calculated repeat-purchase and CLV measures.

## 📌 Suggested Next Steps
- Swap in the real Olist or Superstore dataset (same column names) for a live portfolio piece.
- Add a demand-forecasting notebook (Prophet / ARIMA) on the monthly revenue series.
- Deploy the Power BI report to the Power BI Service and embed a screenshot/GIF here.
