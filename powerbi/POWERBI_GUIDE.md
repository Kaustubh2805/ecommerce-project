# Power BI Dashboard — Build Guide

This folder (`data_model/`) contains a **star schema**, ready to import directly
into Power BI Desktop: `Get Data → Text/CSV`, load all 6 files.

## 1. Data Model

```
                     ┌───────────────────┐
                     │   dim_date         │
                     │   date_key (PK)    │
                     └─────────▲──────────┘
                               │
┌────────────────┐   ┌────────┴─────────┐   ┌──────────────────┐
│ dim_customers   │◄──┤   fact_sales      ├──►│ dim_products      │
│ customer_id(PK) │   │ order_id          │   │ product_id (PK)   │
└────────────────┘   │ customer_id (FK)  │   └──────────────────┘
                      │ product_id (FK)   │
┌───────────────────┐│ order_date (FK)   │   ┌──────────────────┐
│ dim_customer_      ││ quantity, sales,  │   │ dim_returns       │
│ segments            ││ profit, discount  │   │ order_id (FK)     │
│ customer_id (FK)   │└───────────────────┘   └──────────────────┘
└───────────────────┘
```

**Relationships to create in Model view:**
| From | To | Cardinality | Cross-filter |
|---|---|---|---|
| `fact_sales[customer_id]` | `dim_customers[customer_id]` | Many-to-1 | Single |
| `fact_sales[product_id]` | `dim_products[product_id]` | Many-to-1 | Single |
| `fact_sales[order_date]` | `dim_date[date]` | Many-to-1 | Single |
| `dim_customer_segments[customer_id]` | `dim_customers[customer_id]` | 1-to-1 | Single |
| `dim_returns[order_id]` | `fact_sales[order_id]` | Many-to-1 | Single |

Mark **`dim_date`** as a Date Table: `Table tools → Mark as date table → date`.

## 2. Core DAX Measures

Create a dedicated measures table (`New Table` → name it `_Measures`), then add:

```DAX
Total Revenue = SUM(fact_sales[sales])

Total Profit = SUM(fact_sales[profit])

Profit Margin % = DIVIDE([Total Profit], [Total Revenue])

Total Orders = DISTINCTCOUNT(fact_sales[order_id])

Total Customers = DISTINCTCOUNT(fact_sales[customer_id])

Avg Order Value = DIVIDE([Total Revenue], [Total Orders])

Units Sold = SUM(fact_sales[quantity])

Return Rate % =
DIVIDE(
    DISTINCTCOUNT(dim_returns[order_id]),
    [Total Orders]
)

-- Time intelligence (requires dim_date marked as Date Table)
Revenue LY = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_date[date]))

Revenue YoY % = DIVIDE([Total Revenue] - [Revenue LY], [Revenue LY])

Revenue MTD = TOTALMTD([Total Revenue], dim_date[date])

Rolling 3M Revenue =
CALCULATE(
    [Total Revenue],
    DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -3, MONTH)
)

-- Customer analytics
Repeat Customers =
CALCULATE(
    DISTINCTCOUNT(fact_sales[customer_id]),
    FILTER(
        VALUES(fact_sales[customer_id]),
        CALCULATE(DISTINCTCOUNT(fact_sales[order_id])) >= 2
    )
)

Repeat Purchase Rate % = DIVIDE([Repeat Customers], [Total Customers])

CLV (Avg) = DIVIDE([Total Revenue], [Total Customers])

-- Discount / margin impact
Avg Discount % = AVERAGE(fact_sales[discount])

Gross Sales (Pre-Discount) = SUMX(fact_sales, fact_sales[quantity] * fact_sales[unit_price])

Discount Amount = [Gross Sales (Pre-Discount)] - [Total Revenue]
```

## 3. Recommended Pages & Visuals

| Page | Visuals |
|---|---|
| **Executive Overview** | KPI cards (Revenue, Profit, Orders, AOV, Margin %), line chart Revenue/Profit by month, map by region, YoY % card |
| **Sales Analysis** | Bar: revenue by category/sub-category; matrix: region × segment; discount-band vs margin chart; ship-mode performance |
| **Product Performance** | Top-N products table (sortable), scatter: revenue vs margin per product, return-rate by category |
| **Customer Analytics** | RFM segment treemap/bar, cluster scatter (frequency vs monetary), cohort retention matrix (use the `cohort_retention.csv` from the Python output as a supporting table or recreate with DAX), top-20 customers table |
| **Filters (all pages)** | Slicers: date range, region, segment, category, rfm_segment |

## 4. Import Notes
- `dim_date.csv` already contains `year`, `month_name`, `quarter`, `is_weekend` columns — build a sort-by-column for `month_name` using `month_num` so months display chronologically, not alphabetically.
- `dim_customer_segments.csv` (RFM tiers + K-Means cluster names) comes straight from `python/02_customer_segmentation.py` — refresh that script and re-export if the underlying data changes.
- For the cohort retention heatmap visual, import `data/cohort_retention.csv` directly (already pivoted by cohort month × month-index) — it's easiest to build this visual from the pre-computed matrix rather than re-deriving it in DAX.
