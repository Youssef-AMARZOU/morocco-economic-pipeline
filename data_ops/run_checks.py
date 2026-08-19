"""
Morocco Economic Pipeline - Data Ops Orchestrator
Runs all validation, SLA, observability, and alerting checks.
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "tests"))
sys.path.insert(0, str(Path(__file__).parent / "alerts"))

from validate_tables import run_validation
from check_slas import check_freshness, check_volume, generate_sla_report
from observe_data import run_observability
from alert_manager import AlertManager, PipelineMonitor

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

DATA_DIR = Path(__file__).parent.parent / "kaggle_full_upload"


def run_all_checks(data_dir=None):
    data_dir = data_dir or DATA_DIR
    print("=" * 70)
    print("MOROCCO PIPELINE - FULL DATA OPS CHECK")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Data dir: {data_dir}")
    print("=" * 70)

    am = AlertManager()
    mon = PipelineMonitor(am)
    mon.on_pipeline_start("data_ops_check")

    # 1. Validation
    print("\n" + "=" * 50)
    print("1. TABLE VALIDATION")
    print("=" * 50)
    val_success = run_validation()

    # 2. SLAs
    print("\n" + "=" * 50)
    print("2. FRESHNESS & VOLUME SLAs")
    print("=" * 50)
    fr = check_freshness(data_dir)
    vr = check_volume(data_dir)
    sla_report = generate_sla_report(fr, vr)

    # 3. Observability
    print("\n" + "=" * 50)
    print("3. DATA OBSERVABILITY")
    print("=" * 50)
    obs_report = run_observability(data_dir)

    # 4. Alerts
    print("\n" + "=" * 50)
    print("4. ALERT SUMMARY")
    print("=" * 50)
    mon.on_pipeline_end("data_ops_check", success=val_success)
    alert_report = mon.save()

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  Validation: {'PASS' if val_success else 'FAIL'}")
    print(f"  Freshness SLA: {sla_report['freshness']['passed']}/{sla_report['freshness']['total']}")
    print(f"  Volume SLA: {sla_report['volume']['passed']}/{sla_report['volume']['total']}")
    print(f"  Observability: {obs_report['critical']} critical, {obs_report['warnings']} warnings")
    print(f"  Alerts: {alert_report['critical']} critical, {alert_report['warnings']} warnings")
    print("=" * 70)

    return {
        "validation": val_success,
        "sla": sla_report,
        "observability": obs_report,
        "alerts": alert_report,
    }


if __name__ == "__main__":
    import sys
    data_dir = DATA_DIR
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    results = run_all_checks(data_dir)
