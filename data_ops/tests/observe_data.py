"""
Morocco Economic Pipeline - Data Observability
Automated checks for anomalies, volume drops, schema changes, and null values.
"""
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

THRESHOLDS = {
    "z_score": 3.0,
    "null_pct_warn": 5.0,
    "null_pct_critical": 20.0,
    "volume_drop_pct": 30.0,
    "schema_change_critical": True,
}


class DataObservability:
    def __init__(self):
        self.alerts = []

    def _alert(self, severity, category, table, message, details=None):
        alert = {
            "severity": severity,
            "category": category,
            "table": table,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }
        self.alerts.append(alert)
        icon = {"CRITICAL": "!!!", "WARNING": " ! ", "INFO": " i "}.get(severity, "   ")
        print(f"  [{icon}] [{severity}] {table}: {message}")

    def check_anomalies(self, df, table_name):
        """Detect statistical anomalies using Z-score."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) < 10:
                continue
            mean = data.mean()
            std = data.std()
            if std == 0:
                continue
            z_scores = np.abs((data - mean) / std)
            anomalies = (z_scores > THRESHOLDS["z_score"]).sum()
            if anomalies > 0:
                pct = anomalies / len(data) * 100
                severity = "CRITICAL" if pct > 10 else "WARNING"
                self._alert(severity, "ANOMALY", table_name,
                           f"{col}: {anomalies} anomalous values ({pct:.1f}%)",
                           {"column": col, "count": int(anomalies), "pct": round(pct, 2),
                            "mean": round(mean, 4), "std": round(std, 4)})
            else:
                self._alert("INFO", "ANOMALY", table_name,
                           f"{col}: no anomalies detected")

    def check_nulls(self, df, table_name):
        """Monitor null value patterns."""
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = null_count / len(df) * 100
            if null_pct >= THRESHOLDS["null_pct_critical"]:
                self._alert("CRITICAL", "NULL", table_name,
                           f"{col}: {null_pct:.1f}% nulls (>= {THRESHOLDS['null_pct_critical']}%)",
                           {"column": col, "null_pct": round(null_pct, 2)})
            elif null_pct >= THRESHOLDS["null_pct_warn"]:
                self._alert("WARNING", "NULL", table_name,
                           f"{col}: {null_pct:.1f}% nulls (>= {THRESHOLDS['null_pct_warn']}%)",
                           {"column": col, "null_pct": round(null_pct, 2)})

    def check_volume(self, df, table_name, expected_rows=None):
        """Detect sudden volume drops."""
        actual = len(df)
        if expected_rows is None:
            return
        drop_pct = (expected_rows - actual) / expected_rows * 100
        if drop_pct > THRESHOLDS["volume_drop_pct"]:
            self._alert("CRITICAL", "VOLUME", table_name,
                       f"Volume drop: {actual} rows (expected {expected_rows}, -{drop_pct:.1f}%)",
                       {"actual": actual, "expected": expected_rows, "drop_pct": round(drop_pct, 2)})
        elif drop_pct > 10:
            self._alert("WARNING", "VOLUME", table_name,
                       f"Volume decline: {actual} rows (expected {expected_rows}, -{drop_pct:.1f}%)",
                       {"actual": actual, "expected": expected_rows, "drop_pct": round(drop_pct, 2)})

    def check_schema(self, df, table_name, expected_columns):
        """Detect schema changes."""
        actual = set(df.columns)
        expected = set(expected_columns)
        missing = expected - actual
        added = actual - expected

        if missing:
            self._alert("CRITICAL", "SCHEMA", table_name,
                       f"Missing columns: {missing}",
                       {"missing": list(missing)})
        if added:
            self._alert("WARNING", "SCHEMA", table_name,
                       f"New columns detected: {added}",
                       {"added": list(added)})
        if not missing and not added:
            self._alert("INFO", "SCHEMA", table_name, "Schema intact")

    def check_distributions(self, df, table_name, baseline_stats=None):
        """Compare current distributions against baseline."""
        if baseline_stats is None:
            return
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in baseline_stats:
                continue
            current_mean = df[col].mean()
            baseline_mean = baseline_stats[col]["mean"]
            baseline_std = baseline_stats[col]["std"]
            if baseline_std == 0:
                continue
            z = abs(current_mean - baseline_mean) / baseline_std
            if z > THRESHOLDS["z_score"]:
                self._alert("WARNING", "DRIFT", table_name,
                           f"{col}: mean shifted ({current_mean:.2f} vs baseline {baseline_mean:.2f}, z={z:.2f})",
                           {"column": col, "current_mean": round(current_mean, 4),
                            "baseline_mean": round(baseline_mean, 4), "z_score": round(z, 2)})

    def save_alerts(self):
        path = RESULTS_DIR / f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_alerts": len(self.alerts),
            "critical": sum(1 for a in self.alerts if a["severity"] == "CRITICAL"),
            "warnings": sum(1 for a in self.alerts if a["severity"] == "WARNING"),
            "info": sum(1 for a in self.alerts if a["severity"] == "INFO"),
            "alerts": self.alerts,
        }
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nAlerts saved: {path}")
        return report


EXPECTED_SCHEMAS = {
    "indicators_clean": ["year"],
    "dim_indicators": ["indicator_code", "indicator_name", "category", "source"],
    "master_dataset": ["year"],
    "benchmark_morocco": ["year"],
}

EXPECTED_ROWS = {
    "indicators_clean": 72,
    "master_dataset": 54,
    "dim_indicators": 120,
    "benchmark_morocco": 30,
}


def run_observability(data_dir):
    print("=" * 60)
    print("MOROCCO PIPELINE - DATA OBSERVABILITY")
    print("=" * 60)

    obs = DataObservability()
    data_path = Path(data_dir)

    for csv_file in data_path.glob("*.csv"):
        table_name = csv_file.stem
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            obs._alert("CRITICAL", "LOAD", table_name, f"Cannot load: {e}")
            continue

        print(f"\n--- {table_name} ({len(df)} rows, {len(df.columns)} cols) ---")

        obs.check_nulls(df, table_name)
        obs.check_anomalies(df, table_name)
        obs.check_volume(df, table_name, EXPECTED_ROWS.get(table_name))

        if table_name in EXPECTED_SCHEMAS:
            obs.check_schema(df, table_name, EXPECTED_SCHEMAS[table_name])

    report = obs.save_alerts()
    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {report['critical']} critical, {report['warnings']} warnings, {report['info']} info")
    print(f"{'=' * 60}")
    return report


if __name__ == "__main__":
    import sys
    data_dir = Path(__file__).parent.parent / "kaggle_full_upload"
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    run_observability(data_dir)
