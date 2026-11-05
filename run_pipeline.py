"""
run_pipeline.py
Master End-to-End Orchestrator for the E-Commerce Analytics Project.

Executes all pipeline stages in strict order:
  1. (Optional) Synthetic Data Generation
  2. Relational Database Build & Ingestion (SQLite)
  3. Data Quality Checks & Exploratory Data Analysis (EDA)
  4. Customer Segmentation (RFM + K-Means) & Cohort Retention
  5. Predictive Time-Series Revenue Forecasting
  6. Market Basket Analysis & Product Affinity
  7. Power BI Star-Schema Model Generation & Synchronization
  8. Analytical SQL Business Query Verification
  9. Automated Data Pipeline Test Suite
"""
import sys
import time
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_step(step_num, total_steps, description, script_path, extra_args=None):
    print("\n" + "=" * 80)
    print(f"[{step_num}/{total_steps}] {description.upper()}")
    print(f"Running: {script_path}")
    print("=" * 80)
    start_time = time.time()

    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    elapsed = time.time() - start_time

    if result.returncode != 0:
        print(f"\n❌ STEP FAILED: {description} (exit code {result.returncode})")
        sys.exit(result.returncode)

    print(f"✅ Completed in {elapsed:.2f}s")
    return elapsed

def main():
    parser = argparse.ArgumentParser(description="Run the end-to-end e-commerce analytics pipeline.")
    parser.add_argument("--regenerate-data", action="store_true", help="Regenerate raw synthetic CSV files before running pipeline.")
    args = parser.parse_args()

    print("\n" + "#" * 80)
    print("  E-COMMERCE SALES & CUSTOMER ANALYTICS — END-TO-END PIPELINE")
    print("#" * 80)
    pipeline_start = time.time()

    steps = []
    if args.regenerate_data:
        steps.append(("Generate Synthetic Raw Data", BASE_DIR / "python" / "generate_data.py"))

    steps.extend([
        ("Build SQLite Relational Database", BASE_DIR / "python" / "build_database.py"),
        ("Data Quality QA & Exploratory Analysis", BASE_DIR / "python" / "01_data_cleaning_eda.py"),
        ("Customer Segmentation (RFM/K-Means) & Cohorts", BASE_DIR / "python" / "02_customer_segmentation.py"),
        ("Time-Series Revenue Forecasting", BASE_DIR / "python" / "03_revenue_forecasting.py"),
        ("Market Basket Analysis & Product Affinity", BASE_DIR / "python" / "04_market_basket_analysis.py"),
        ("Build & Synchronize Power BI Star Schema", BASE_DIR / "python" / "build_powerbi_model.py"),
        ("Execute 14 SQL Analytical Queries", BASE_DIR / "python" / "run_sql_analysis.py"),
    ])

    timings = {}
    total = len(steps) + 1  # plus test suite
    for i, (desc, path) in enumerate(steps, 1):
        elapsed = run_step(i, total, desc, path)
        timings[desc] = elapsed

    # Run Unit Test Suite
    test_start = time.time()
    print("\n" + "=" * 80)
    print(f"[{total}/{total}] RUN AUTOMATED DATA PIPELINE TESTS")
    print("=" * 80)
    test_cmd = [sys.executable, "-m", "unittest", "tests/test_data_pipeline.py"]
    test_res = subprocess.run(test_cmd, cwd=str(BASE_DIR))
    if test_res.returncode != 0:
        print("\n❌ Pipeline tests failed!")
        sys.exit(test_res.returncode)
    timings["Automated Data Pipeline Tests"] = time.time() - test_start

    total_elapsed = time.time() - pipeline_start

    print("\n" + "#" * 80)
    print("  PIPELINE EXECUTION SUMMARY")
    print("#" * 80)
    for desc, dur in timings.items():
        print(f"  • {desc:<48}: {dur:6.2f}s")
    print("-" * 80)
    print(f"  Total Pipeline Runtime: {total_elapsed:.2f}s")
    print("  Status: ALL STAGES COMPLETED & SYNCHRONIZED SUCCESSFULLY 🎉")
    print("#" * 80 + "\n")

if __name__ == "__main__":
    main()
