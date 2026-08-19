"""
Morocco Economic Pipeline - Freshness & Latency SLA Configuration
Defines time thresholds for KPI data freshness in BI tools.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════
# SLA DEFINITIONS
# ══════════════════════════════════════════════════════════
SLA_CONFIG = {
    "pipeline_name": "morocco-economic-pipeline",
    "version": "1.0",
    "updated": datetime.now().isoformat(),

    "freshness_slas": {
        "critical": {
            "description": "Must be fresh within hours - real-time dashboards",
            "max_age_hours": 6,
            "tables": [
                "bank_prices",
                "indicators_clean",
            ],
            "alert_on_breach": True,
            "escalation": "immediate",
        },
        "standard": {
            "description": "Must be fresh within 1 day - daily reports",
            "max_age_hours": 24,
            "tables": [
                "master_dataset",
                "benchmark_morocco",
            ],
            "alert_on_breach": True,
            "escalation": "within_1_hour",
        },
        "batch": {
            "description": "Must be fresh within 1 week - weekly analytics",
            "max_age_hours": 168,
            "tables": [
                "dim_indicators",
            ],
            "alert_on_breach": True,
            "escalation": "within_4_hours",
        },
    },

    "latency_slas": {
        "etl_pipeline": {
            "description": "Full ETL must complete within time window",
            "max_duration_minutes": 30,
            "stages": {
                "fetch_wb": {"max_minutes": 10},
                "fetch_owid": {"max_minutes": 10},
                "clean_transform": {"max_minutes": 5},
                "merge_load": {"max_minutes": 5},
            },
        },
        "r_kernel": {
            "description": "R analysis pipeline on Kaggle",
            "max_duration_minutes": 60,
            "stages": {
                "ingestion": {"max_minutes": 5},
                "eda": {"max_minutes": 10},
                "ml_dl": {"max_minutes": 20},
                "report": {"max_minutes": 5},
            },
        },
    },

    "volume_slas": {
        "indicators_clean": {"min_rows": 50, "max_rows": 100, "expected": 72},
        "master_dataset": {"min_rows": 40, "max_rows": 100, "expected": 54},
        "dim_indicators": {"min_rows": 10, "max_rows": 200, "expected": 120},
        "bank_prices": {"min_rows": 100, "max_rows": 50000, "expected": 5000},
        "benchmark_morocco": {"min_rows": 10, "max_rows": 100, "expected": 30},
    },

    "quality_slas": {
        "null_threshold_pct": 5.0,
        "duplicate_threshold_pct": 0.0,
        "schema_change_detection": True,
        "anomaly_z_score_threshold": 3.0,
    },
}


def check_freshness(data_dir):
    """Check all tables against freshness SLAs."""
    print("=" * 60)
    print("FRESHNESS SLA CHECK")
    print("=" * 60)

    results = []
    data_path = Path(data_dir)

    for sla_name, sla in SLA_CONFIG["freshness_slas"].items():
        print(f"\n[{sla_name.upper()}] {sla['description']}")
        print(f"  Max age: {sla['max_age_hours']}h")

        for table in sla["tables"]:
            csv_path = data_path / f"{table}.csv"
            if not csv_path.exists():
                print(f"  [MISSING] {table}.csv")
                results.append({"table": table, "sla": sla_name, "status": "MISSING"})
                continue

            mtime = datetime.fromtimestamp(csv_path.stat().st_mtime)
            age_hours = (datetime.now() - mtime).total_seconds() / 3600
            passed = age_hours <= sla["max_age_hours"]

            status = "FRESH" if passed else "STALE"
            print(f"  [{status}] {table}: age={age_hours:.1f}h (SLA={sla['max_age_hours']}h)")
            results.append({
                "table": table,
                "sla": sla_name,
                "status": status,
                "age_hours": round(age_hours, 1),
                "sla_hours": sla["max_age_hours"],
            })

    passed = sum(1 for r in results if r["status"] == "FRESH")
    total = len(results)
    print(f"\nFreshness: {passed}/{total} tables within SLA")
    return results


def check_volume(data_dir):
    """Check all tables against volume SLAs."""
    print("\n" + "=" * 60)
    print("VOLUME SLA CHECK")
    print("=" * 60)

    import pandas as pd
    results = []
    data_path = Path(data_dir)

    for table, sla in SLA_CONFIG["volume_slas"].items():
        csv_path = data_path / f"{table}.csv"
        if not csv_path.exists():
            print(f"  [MISSING] {table}")
            continue

        df = pd.read_csv(csv_path)
        actual = len(df)
        passed = sla["min_rows"] <= actual <= sla["max_rows"]
        status = "OK" if passed else "BREACH"
        print(f"  [{status}] {table}: {actual} rows (expected ~{sla['expected']}, range=[{sla['min_rows']}, {sla['max_rows']}])")
        results.append({
            "table": table,
            "actual": actual,
            "expected": sla["expected"],
            "status": status,
        })

    passed = sum(1 for r in results if r["status"] == "OK")
    print(f"\nVolume: {passed}/{len(results)} tables within SLA")
    return results


def generate_sla_report(freshness_results, volume_results):
    """Generate SLA compliance report."""
    report = {
        "pipeline": SLA_CONFIG["pipeline_name"],
        "timestamp": datetime.now().isoformat(),
        "freshness": {
            "total": len(freshness_results),
            "passed": sum(1 for r in freshness_results if r["status"] == "FRESH"),
            "details": freshness_results,
        },
        "volume": {
            "total": len(volume_results),
            "passed": sum(1 for r in volume_results if r["status"] == "OK"),
            "details": volume_results,
        },
    }

    path = RESULTS_DIR / f"sla_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSLA report saved: {path}")
    return report


if __name__ == "__main__":
    import sys
    data_dir = Path(__file__).parent.parent / "kaggle_full_upload"
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]

    fr = check_freshness(data_dir)
    vr = check_volume(data_dir)
    report = generate_sla_report(fr, vr)
    sys.exit(0 if report["freshness"]["passed"] == report["freshness"]["total"] else 1)
