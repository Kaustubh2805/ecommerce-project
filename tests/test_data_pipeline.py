"""
test_data_pipeline.py
Automated test suite validating data integrity, relational constraints,
and business rules across the e-commerce analytics pipeline.
Run with: python -m unittest tests/test_data_pipeline.py
"""
import unittest
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ecommerce.db"

class TestDataPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.customers = pd.read_csv(DATA_DIR / "dim_customers.csv")
        cls.products = pd.read_csv(DATA_DIR / "dim_products.csv")
        cls.orders = pd.read_csv(DATA_DIR / "fact_orders.csv", parse_dates=["order_date", "ship_date"])
        cls.items = pd.read_csv(DATA_DIR / "fact_order_items.csv")
        cls.returns = pd.read_csv(DATA_DIR / "fact_returns.csv")

    def test_required_files_exist(self):
        """Verify that all core database and data files exist."""
        required = [
            DATA_DIR / "dim_customers.csv",
            DATA_DIR / "dim_products.csv",
            DATA_DIR / "fact_orders.csv",
            DATA_DIR / "fact_order_items.csv",
            DATA_DIR / "fact_returns.csv",
            DB_PATH
        ]
        for f in required:
            self.assertTrue(f.exists(), f"Missing required file: {f}")

    def test_referential_integrity(self):
        """Validate foreign key relationships across fact and dimension tables."""
        # 1. Every order belongs to a valid customer
        orphan_orders = self.orders[~self.orders["customer_id"].isin(self.customers["customer_id"])]
        self.assertEqual(len(orphan_orders), 0, f"Found {len(orphan_orders)} orphan orders without customer.")

        # 2. Every line item belongs to a valid order
        orphan_items = self.items[~self.items["order_id"].isin(self.orders["order_id"])]
        self.assertEqual(len(orphan_items), 0, f"Found {len(orphan_items)} orphan items without parent order.")

        # 3. Every line item references an existing product
        orphan_products = self.items[~self.items["product_id"].isin(self.products["product_id"])]
        self.assertEqual(len(orphan_products), 0, f"Found {len(orphan_products)} orphan items with invalid product_id.")

        # 4. Every return references an existing order
        orphan_returns = self.returns[~self.returns["order_id"].isin(self.orders["order_id"])]
        self.assertEqual(len(orphan_returns), 0, f"Found {len(orphan_returns)} orphan returns without order.")

    def test_business_and_logical_constraints(self):
        """Ensure transactions adhere to physical retail logic."""
        # Shipping must not occur before order placement
        invalid_shipping = self.orders[self.orders["ship_date"] < self.orders["order_date"]]
        self.assertEqual(len(invalid_shipping), 0, "Found orders shipped before placement date.")

        # Quantities must be positive integers
        invalid_qty = self.items[self.items["quantity"] <= 0]
        self.assertEqual(len(invalid_qty), 0, "Found non-positive item quantities.")

        # Sales must be positive
        invalid_sales = self.items[self.items["sales"] <= 0]
        self.assertEqual(len(invalid_sales), 0, "Found non-positive sales values.")

        # Discounts must be bounded between 0% and 100%
        invalid_discount = self.items[(self.items["discount"] < 0) | (self.items["discount"] > 1.0)]
        self.assertEqual(len(invalid_discount), 0, "Found discounts outside [0, 1] range.")

    def test_database_connectivity_and_tables(self):
        """Test SQLite database connection and verify table row counts."""
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]

        for expected in ["dim_customers", "dim_products", "fact_orders", "fact_order_items", "fact_returns"]:
            self.assertIn(expected, tables, f"Table {expected} missing in database.")

        cur.execute("SELECT COUNT(*) FROM fact_orders;")
        count = cur.fetchone()[0]
        self.assertGreater(count, 0, "Database fact_orders table is empty.")
        conn.close()

if __name__ == "__main__":
    unittest.main()

