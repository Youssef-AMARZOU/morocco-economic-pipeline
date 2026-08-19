"""
Morocco Economic Pipeline - Data Validation Tests
Validates fact/dimension tables against business rules and source intent.
"""
import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATASET_DIR = Path(__file__).parent.parent / "kaggle_full_upload"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


class ValidationResult:
    def __init__(self, test_name, passed, message, details=None):
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            "test": self.test_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class DataValidator:
    def __init__(self):
        self.results = []
        self.errors = []

    def _add(self, result):
        self.results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.test_name}: {result.message}")

    def validate_not_null(self, df, columns, table_name):
        for col in columns:
            if col not in df.columns:
                self._add(ValidationResult(
                    f"{table_name}.{col}_exists", False,
                    f"Column {col} missing from {table_name}"
                ))
                continue
            null_count = df[col].isnull().sum()
            null_pct = null_count / len(df) * 100
            passed = null_pct < 5
            self._add(ValidationResult(
                f"{table_name}.{col}_not_null", passed,
                f"{col}: {null_count} nulls ({null_pct:.1f}%)",
                {"null_count": int(null_count), "null_pct": round(null_pct, 2)}
            ))

    def validate_unique(self, df, columns, table_name):
        for col in columns:
            if col not in df.columns:
                continue
            dup_count = df[col].duplicated().sum()
            passed = dup_count == 0
            self._add(ValidationResult(
                f"{table_name}.{col}_unique", passed,
                f"{col}: {dup_count} duplicates",
                {"duplicate_count": int(dup_count)}
            ))

    def validate_range(self, df, column, min_val, max_val, table_name):
        if column not in df.columns:
            return
        col_data = df[column].dropna()
        below = (col_data < min_val).sum()
        above = (col_data > max_val).sum()
        violations = below + above
        passed = violations == 0
        self._add(ValidationResult(
            f"{table_name}.{column}_range", passed,
            f"{column}: {violations} values outside [{min_val}, {max_val}]",
            {"below_min": int(below), "above_max": int(above)}
        ))

    def validate_referential(self, df, fk_col, ref_df, ref_col, table_name):
        if fk_col not in df.columns or ref_col not in ref_df.columns:
            return
        missing = set(df[fk_col].dropna()) - set(ref_df[ref_col].dropna())
        passed = len(missing) == 0
        self._add(ValidationResult(
            f"{table_name}.{fk_col}_referential", passed,
            f"{fk_col}: {len(missing)} orphan references",
            {"missing_refs": list(missing)[:10]}
        ))

    def validate_freshness(self, df, date_col, max_age_days, table_name):
        if date_col not in df.columns:
            return
        try:
            dates = pd.to_datetime(df[date_col])
            latest = dates.max()
            age = (datetime.now() - latest).days
            passed = age <= max_age_days
            self._add(ValidationResult(
                f"{table_name}_freshness", passed,
                f"Latest {date_col}: {latest.date()} (age={age}d, SLA={max_age_days}d)",
                {"latest_date": str(latest.date()), "age_days": age, "sla_days": max_age_days}
            ))
        except Exception as e:
            self._add(ValidationResult(
                f"{table_name}_freshness", False, f"Cannot parse dates: {e}"
            ))

    def validate_volume(self, df, expected_min, expected_max, table_name):
        actual = len(df)
        passed = expected_min <= actual <= expected_max
        self._add(ValidationResult(
            f"{table_name}_volume", passed,
            f"Rows: {actual} (expected [{expected_min}, {expected_max}])",
            {"actual": actual, "expected_min": expected_min, "expected_max": expected_max}
        ))

    def validate_schema(self, df, expected_cols, table_name):
        actual = set(df.columns)
        expected = set(expected_cols)
        missing = expected - actual
        extra = actual - expected
        passed = len(missing) == 0
        self._add(ValidationResult(
            f"{table_name}_schema", passed,
            f"Missing: {missing or 'none'}, Extra: {extra or 'none'}",
            {"missing": list(missing), "extra": list(extra)}
        ))

    def validate_no_constant(self, df, exclude_cols, table_name):
        for col in df.columns:
            if col in exclude_cols:
                continue
            if df[col].nunique() <= 1:
                self._add(ValidationResult(
                    f"{table_name}.{col}_non_constant", False,
                    f"{col} is constant (single value)"
                ))

    def validate_correlation(self, df, col1, col2, min_corr, table_name):
        if col1 not in df.columns or col2 not in df.columns:
            return
        corr = df[[col1, col2]].dropna().corr().iloc[0, 1]
        passed = abs(corr) >= min_corr
        self._add(ValidationResult(
            f"{table_name}.{col1}_{col2}_correlation", passed,
            f"Corr({col1}, {col2}) = {corr:.3f} (min={min_corr})",
            {"correlation": round(corr, 4)}
        ))

    def summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }

    def save_results(self):
        report = {
            "summary": self.summary(),
            "results": [r.to_dict() for r in self.results],
        }
        path = RESULTS_DIR / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nResults saved: {path}")
        return report


def run_validation():
    print("=" * 60)
    print("MOROCCO PIPELINE - DATA VALIDATION TESTS")
    print("=" * 60)

    v = DataValidator()

    # Load all CSVs
    csvs = {}
    for f in DATASET_DIR.glob("*.csv"):
        try:
            csvs[f.stem] = pd.read_csv(f)
        except Exception as e:
            print(f"  [ERROR] Cannot load {f.name}: {e}")

    print(f"\nLoaded {len(csvs)} CSVs: {list(csvs.keys())}")

    # ═══ INDICATORS (Fact table) ═══
    if "indicators_clean" in csvs:
        print("\n--- indicators_clean (Fact) ---")
        df = csvs["indicators_clean"]
        v.validate_not_null(df, ["year"], "indicators")
        v.validate_range(df, "year", 1960, 2030, "indicators")
        v.validate_volume(df, 50, 100, "indicators")
        v.validate_no_constant(df, ["year"], "indicators")

    # ═══ DIM_INDICATORS (Dimension) ═══
    if "dim_indicators" in csvs:
        print("\n--- dim_indicators (Dimension) ---")
        df = csvs["dim_indicators"]
        v.validate_not_null(df, ["indicator_code", "indicator_name"], "dim_indicators")
        v.validate_unique(df, ["indicator_code"], "dim_indicators")
        v.validate_volume(df, 10, 200, "dim_indicators")

    # ═══ MASTER_DATASET (Aggregated) ═══
    if "master_dataset" in csvs:
        print("\n--- master_dataset (Aggregated) ---")
        df = csvs["master_dataset"]
        v.validate_not_null(df, ["year"], "master")
        v.validate_range(df, "year", 1960, 2030, "master")
        v.validate_volume(df, 40, 100, "master")
        v.validate_freshness(df, "year", 365, "master")

    # ═══ BANK_PRICES (Financial) ═══
    if "bank_prices" in csvs:
        print("\n--- bank_prices (Financial) ---")
        df = csvs["bank_prices"]
        v.validate_not_null(df, ["date"], "bank_prices")
        v.validate_volume(df, 100, 50000, "bank_prices")
        v.validate_freshness(df, "date", 365, "bank_prices")

    # ═══ BENCHMARK_MOROCCO ═══
    if "benchmark_morocco" in csvs:
        print("\n--- benchmark_morocco (Reference) ---")
        df = csvs["benchmark_morocco"]
        v.validate_not_null(df, ["year"], "benchmark")
        v.validate_volume(df, 10, 100, "benchmark")

    # ═══ CROSS-TABLE VALIDATION ═══
    print("\n--- Cross-table validation ---")
    if "indicators_clean" in csvs and "dim_indicators" in csvs:
        ind = csvs["indicators_clean"]
        dim = csvs["dim_indicators"]
        ind_cols = set(ind.columns) - {"year"}
        dim_codes = set(dim["indicator_code"]) if "indicator_code" in dim.columns else set()
        missing_in_dim = ind_cols - dim_codes
        v._add(ValidationResult(
            "cross_table_coverage", len(missing_in_dim) == 0,
            f"Indicators without dim: {len(missing_in_dim)}",
            {"missing": list(missing_in_dim)[:10]}
        ))

    # Summary
    print("\n" + "=" * 60)
    summary = v.summary()
    print(f"RESULTS: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']}%)")
    if summary["failed"] > 0:
        print(f"FAILED TESTS:")
        for r in v.results:
            if not r.passed:
                print(f"  - {r.test_name}: {r.message}")
    print("=" * 60)

    report = v.save_results()
    return report["summary"]["failed"] == 0


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
