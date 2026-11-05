-- ============================================================================
-- E-Commerce Sales & Customer Analysis
-- Schema Definition (SQLite dialect; portable to PostgreSQL/MySQL with minor
-- type changes noted in comments)
-- ============================================================================

DROP TABLE IF EXISTS fact_returns;
DROP TABLE IF EXISTS fact_order_items;
DROP TABLE IF EXISTS fact_orders;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_customers;

CREATE TABLE dim_customers (
    customer_id     TEXT PRIMARY KEY,
    customer_name   TEXT NOT NULL,
    email           TEXT,
    segment         TEXT CHECK (segment IN ('Consumer','Corporate','Home Office')),
    region          TEXT,
    city            TEXT,
    state           TEXT,
    signup_date     DATE
);

CREATE TABLE dim_products (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT NOT NULL,
    category        TEXT,
    sub_category    TEXT,
    unit_price      REAL,
    unit_cost       REAL
);

CREATE TABLE fact_orders (
    order_id        TEXT PRIMARY KEY,
    customer_id     TEXT REFERENCES dim_customers(customer_id),
    order_date      DATE NOT NULL,
    ship_date       DATE,
    ship_mode       TEXT,
    order_total     REAL
);

CREATE TABLE fact_order_items (
    order_item_id   INTEGER PRIMARY KEY,
    order_id        TEXT REFERENCES fact_orders(order_id),
    product_id      TEXT REFERENCES dim_products(product_id),
    quantity        INTEGER,
    unit_price      REAL,
    discount        REAL,
    sales           REAL,
    profit          REAL
);

CREATE TABLE fact_returns (
    order_id        TEXT REFERENCES fact_orders(order_id),
    return_date     DATE,
    return_reason   TEXT
);

-- Helpful indexes for analytical joins
CREATE INDEX idx_orders_customer ON fact_orders(customer_id);
CREATE INDEX idx_orders_date ON fact_orders(order_date);
CREATE INDEX idx_items_order ON fact_order_items(order_id);
CREATE INDEX idx_items_product ON fact_order_items(product_id);
CREATE INDEX idx_returns_order ON fact_returns(order_id);
