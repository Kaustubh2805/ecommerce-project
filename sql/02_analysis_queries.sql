-- ============================================================================
-- E-Commerce Sales & Customer Analysis — Analysis Queries
-- Organized into: Sales Performance | Product Analysis | Customer Analytics
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SECTION 1: SALES PERFORMANCE
-- ----------------------------------------------------------------------------

-- 1.1 Monthly revenue, profit and order volume trend
SELECT
    strftime('%Y-%m', o.order_date)                AS month,
    COUNT(DISTINCT o.order_id)                      AS orders,
    ROUND(SUM(oi.sales), 2)                         AS revenue,
    ROUND(SUM(oi.profit), 2)                        AS profit,
    ROUND(SUM(oi.sales) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM fact_orders o
JOIN fact_order_items oi ON oi.order_id = o.order_id
GROUP BY 1
ORDER BY 1;

-- 1.2 Year-over-year growth by month (uses window function LAG)
WITH monthly AS (
    SELECT strftime('%Y', order_date) AS yr,
           strftime('%m', order_date) AS mo,
           SUM(oi.sales) AS revenue
    FROM fact_orders o JOIN fact_order_items oi ON oi.order_id = o.order_id
    GROUP BY 1, 2
)
SELECT
    yr, mo, ROUND(revenue, 2) AS revenue,
    ROUND(LAG(revenue) OVER (PARTITION BY mo ORDER BY yr), 2) AS prev_year_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (PARTITION BY mo ORDER BY yr))
          / NULLIF(LAG(revenue) OVER (PARTITION BY mo ORDER BY yr), 0), 1) AS yoy_growth_pct
FROM monthly
ORDER BY mo, yr;

-- 1.3 Sales & profit by region and customer segment
SELECT
    c.region, c.segment,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(oi.sales), 2)   AS revenue,
    ROUND(SUM(oi.profit), 2)  AS profit,
    ROUND(100.0 * SUM(oi.profit) / NULLIF(SUM(oi.sales),0), 2) AS profit_margin_pct
FROM fact_orders o
JOIN dim_customers c ON c.customer_id = o.customer_id
JOIN fact_order_items oi ON oi.order_id = o.order_id
GROUP BY c.region, c.segment
ORDER BY revenue DESC;

-- 1.4 Ship-mode performance (avg fulfillment days + revenue share)
SELECT
    ship_mode,
    COUNT(*) AS orders,
    ROUND(AVG(julianday(ship_date) - julianday(order_date)), 1) AS avg_fulfillment_days,
    ROUND(SUM(order_total), 2) AS revenue
FROM fact_orders
GROUP BY ship_mode
ORDER BY revenue DESC;

-- 1.5 Discount impact on profit margin (does discounting erode profitability?)
SELECT
    CASE
        WHEN discount = 0 THEN '0%'
        WHEN discount <= 0.10 THEN '1-10%'
        WHEN discount <= 0.20 THEN '11-20%'
        ELSE '21%+'
    END AS discount_band,
    COUNT(*) AS line_items,
    ROUND(SUM(sales), 2) AS revenue,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100.0 * SUM(profit) / NULLIF(SUM(sales),0), 2) AS margin_pct
FROM fact_order_items
GROUP BY 1
ORDER BY 1;

-- ----------------------------------------------------------------------------
-- SECTION 2: PRODUCT ANALYSIS
-- ----------------------------------------------------------------------------

-- 2.1 Top 15 products by revenue
SELECT
    p.product_name, p.category, p.sub_category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.sales), 2) AS revenue,
    ROUND(SUM(oi.profit), 2) AS profit
FROM fact_order_items oi
JOIN dim_products p ON p.product_id = oi.product_id
GROUP BY p.product_id
ORDER BY revenue DESC
LIMIT 15;

-- 2.2 Category & sub-category performance ranked by profit margin
SELECT
    category, sub_category,
    ROUND(SUM(sales), 2) AS revenue,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100.0 * SUM(profit) / NULLIF(SUM(sales), 0), 2) AS margin_pct,
    RANK() OVER (ORDER BY SUM(profit) DESC) AS profit_rank
FROM fact_order_items oi
JOIN dim_products p ON p.product_id = oi.product_id
GROUP BY category, sub_category
ORDER BY profit DESC;

-- 2.3 Products with negative or thin margins (candidates for repricing)
SELECT
    p.product_name, p.category,
    ROUND(SUM(oi.sales), 2) AS revenue,
    ROUND(SUM(oi.profit), 2) AS profit,
    ROUND(100.0 * SUM(oi.profit) / NULLIF(SUM(oi.sales), 0), 2) AS margin_pct
FROM fact_order_items oi
JOIN dim_products p ON p.product_id = oi.product_id
GROUP BY p.product_id
HAVING margin_pct < 5
ORDER BY revenue DESC;

-- 2.4 Return rate by category
SELECT
    p.category,
    COUNT(DISTINCT oi.order_id) AS orders_with_product,
    COUNT(DISTINCT r.order_id) AS returned_orders,
    ROUND(100.0 * COUNT(DISTINCT r.order_id) / NULLIF(COUNT(DISTINCT oi.order_id), 0), 2) AS return_rate_pct
FROM fact_order_items oi
JOIN dim_products p ON p.product_id = oi.product_id
LEFT JOIN fact_returns r ON r.order_id = oi.order_id
GROUP BY p.category
ORDER BY return_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- SECTION 3: CUSTOMER ANALYTICS
-- ----------------------------------------------------------------------------

-- 3.1 RFM (Recency, Frequency, Monetary) base table
-- Reference date = day after the last order in the dataset
WITH ref_date AS (
    SELECT date(MAX(order_date), '+1 day') AS d FROM fact_orders
),
customer_orders AS (
    SELECT
        o.customer_id,
        MAX(o.order_date) AS last_order_date,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.sales) AS monetary
    FROM fact_orders o
    JOIN fact_order_items oi ON oi.order_id = o.order_id
    GROUP BY o.customer_id
)
SELECT
    co.customer_id,
    CAST(julianday((SELECT d FROM ref_date)) - julianday(co.last_order_date) AS INTEGER) AS recency_days,
    co.frequency,
    ROUND(co.monetary, 2) AS monetary,
    NTILE(5) OVER (ORDER BY julianday((SELECT d FROM ref_date)) - julianday(co.last_order_date) DESC) AS r_score,
    NTILE(5) OVER (ORDER BY co.frequency ASC) AS f_score,
    NTILE(5) OVER (ORDER BY co.monetary ASC) AS m_score
FROM customer_orders co
ORDER BY monetary DESC;

-- 3.2 Top 20 customers by lifetime value
SELECT
    c.customer_id, c.customer_name, c.segment, c.region,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.sales), 2) AS lifetime_value,
    ROUND(SUM(oi.sales) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value,
    MIN(o.order_date) AS first_order,
    MAX(o.order_date) AS last_order
FROM dim_customers c
JOIN fact_orders o ON o.customer_id = c.customer_id
JOIN fact_order_items oi ON oi.order_id = o.order_id
GROUP BY c.customer_id
ORDER BY lifetime_value DESC
LIMIT 20;

-- 3.3 Monthly cohort retention (customers grouped by signup/first-purchase month)
WITH first_purchase AS (
    SELECT customer_id, MIN(strftime('%Y-%m', order_date)) AS cohort_month
    FROM fact_orders GROUP BY customer_id
),
activity AS (
    SELECT o.customer_id, fp.cohort_month, strftime('%Y-%m', o.order_date) AS order_month
    FROM fact_orders o JOIN first_purchase fp ON fp.customer_id = o.customer_id
),
cohort_index AS (
    SELECT customer_id, cohort_month, order_month,
        (CAST(strftime('%Y', order_month || '-01') AS INT) * 12 + CAST(strftime('%m', order_month || '-01') AS INT))
        - (CAST(strftime('%Y', cohort_month || '-01') AS INT) * 12 + CAST(strftime('%m', cohort_month || '-01') AS INT))
        AS month_index
    FROM activity
)
SELECT
    cohort_month,
    month_index,
    COUNT(DISTINCT customer_id) AS active_customers
FROM cohort_index
GROUP BY cohort_month, month_index
ORDER BY cohort_month, month_index;

-- 3.4 Repeat purchase rate (customers with 2+ orders / all customers who ordered)
SELECT
    COUNT(DISTINCT customer_id) AS total_customers,
    SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) / COUNT(DISTINCT customer_id), 2) AS repeat_rate_pct
FROM (
    SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
    FROM fact_orders GROUP BY customer_id
);

-- 3.5 Customer segments by simplified RFM tier (using the RFM base from 3.1)
WITH ref_date AS (SELECT date(MAX(order_date), '+1 day') AS d FROM fact_orders),
customer_orders AS (
    SELECT o.customer_id, MAX(o.order_date) AS last_order_date,
           COUNT(DISTINCT o.order_id) AS frequency, SUM(oi.sales) AS monetary
    FROM fact_orders o JOIN fact_order_items oi ON oi.order_id = o.order_id
    GROUP BY o.customer_id
),
scored AS (
    SELECT customer_id,
        NTILE(5) OVER (ORDER BY julianday((SELECT d FROM ref_date)) - julianday(last_order_date) DESC) AS r,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m
    FROM customer_orders
)
SELECT
    CASE
        WHEN r >= 4 AND f >= 4 THEN 'Champions'
        WHEN r >= 3 AND f >= 3 THEN 'Loyal Customers'
        WHEN r >= 4 AND f <= 2 THEN 'New / Promising'
        WHEN r <= 2 AND f >= 4 THEN 'At Risk (was frequent)'
        WHEN r <= 2 AND f <= 2 THEN 'Hibernating / Lost'
        ELSE 'Needs Attention'
    END AS rfm_segment,
    COUNT(*) AS customers
FROM scored
GROUP BY 1
ORDER BY customers DESC;
