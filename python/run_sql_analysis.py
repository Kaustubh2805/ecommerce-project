"""
run_sql_analysis.py
Runs the 14 business queries defined in sql/02_analysis_queries.sql
against data/ecommerce.db and prints the formatted results.
"""
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "ecommerce.db"
SQL_PATH = BASE_DIR / "sql" / "02_analysis_queries.sql"

pd.set_option("display.max_columns", 15)
pd.set_option("display.width", 120)

def main():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    print("=" * 80)
    print("EXECUTING SQL ANALYSIS QUERIES ON E-COMMERCE DATABASE")
    print(f"Database: {DB_PATH.name}")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    with open(SQL_PATH, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split into discrete queries while preserving comments for titles
    query_blocks = []
    current_title = ""
    current_sql = []

    for line in sql_content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("-- 1.") or trimmed.startswith("-- 2.") or trimmed.startswith("-- 3."):
            if current_sql and current_title:
                query_blocks.append((current_title, "\n".join(current_sql)))
                current_sql = []
            current_title = trimmed.lstrip("- ").strip()
        elif not trimmed.startswith("-- ==") and not trimmed.startswith("-- --") and not trimmed.startswith("-- SECTION"):
            current_sql.append(line)

    if current_sql:
        query_blocks.append((current_title, "\n".join(current_sql)))

    success_count = 0
    for idx, (title, sql_text) in enumerate(query_blocks, 1):
        clean_sql = sql_text.strip().rstrip(";")
        if not clean_sql:
            continue

        print(f"\n[{idx}/14] {title}")
        print("-" * 80)
        try:
            df = pd.read_sql_query(clean_sql, conn)
            if len(df) > 10:
                print(df.head(10).to_string(index=False))
                print(f"... ({len(df)} total rows, showing top 10)")
            else:
                print(df.to_string(index=False))
            success_count += 1
        except Exception as e:
            print(f"Query error: {e}")

    conn.close()
    print("\n" + "=" * 80)
    print(f"SQL Execution Summary: {success_count}/{len(query_blocks)} queries ran successfully.")
    print("=" * 80)

if __name__ == "__main__":
    main()

