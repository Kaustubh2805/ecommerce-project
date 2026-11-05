"""
build_database.py
Initializes the SQLite database from sql/01_schema.sql and ingests
the normalized CSV files into their respective relational tables.
Ensures indexes and foreign keys are enforced and synchronized.
"""
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SQL_DIR = BASE_DIR / "sql"
DB_PATH = DATA_DIR / "ecommerce.db"
SCHEMA_PATH = SQL_DIR / "01_schema.sql"

TABLES_TO_LOAD = [
    ("dim_customers", DATA_DIR / "dim_customers.csv"),
    ("dim_products", DATA_DIR / "dim_products.csv"),
    ("fact_orders", DATA_DIR / "fact_orders.csv"),
    ("fact_order_items", DATA_DIR / "fact_order_items.csv"),
    ("fact_returns", DATA_DIR / "fact_returns.csv"),
]

def build_database():
    print("=" * 70)
    print("BUILDING RELATIONAL DATABASE FROM SCHEMA & CSVs")
    print(f"Target DB: {DB_PATH}")
    print("=" * 70)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")

    # Remove existing DB to guarantee a clean, idempotent build
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Execute DDL Schema script
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cur.executescript(schema_sql)
    conn.commit()
    print("Schema created successfully with primary keys and indexes.")

    # 2. Ingest CSV data into tables
    for table_name, csv_path in TABLES_TO_LOAD:
        if not csv_path.exists():
            raise FileNotFoundError(f"Data file {csv_path} missing.")

        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, if_exists="append", index=False)

        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cur.fetchone()[0]
        print(f"  Ingested {row_count:6d} rows into table: {table_name}")

    conn.close()
    print("\nDatabase build complete and verified.")

if __name__ == "__main__":
    build_database()
