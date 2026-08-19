"""
Morocco Economic Pipeline - Alerting Channels
Connects pipeline logs to notification systems for instant error detection.
"""
import json
import smtplib
import logging
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════
# ALERT CONFIGURATION
# ══════════════════════════════════════════════════════════
ALERT_CONFIG = {
    "channels": {
        "log_file": {
            "enabled": True,
            "path": "pipeline.log",
            "level": "INFO",
        },
        "json_log": {
            "enabled": True,
            "path": "alerts.json",
        },
        "email": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender": "",
            "password": "",
            "recipients": [],
        },
        "slack_webhook": {
            "enabled": False,
            "webhook_url": "",
        },
    },
    "severity_routing": {
        "CRITICAL": ["log_file", "json_log", "email", "slack_webhook"],
        "WARNING": ["log_file", "json_log"],
        "INFO": ["log_file"],
    },
}


class AlertManager:
    def __init__(self, config=None):
        self.config = config or ALERT_CONFIG
        self.alerts = []
        self._setup_logging()

    def _setup_logging(self):
        log_path = Path(__file__).parent / self.config["channels"]["log_file"]["path"]
        self.logger = logging.getLogger("morocco_pipeline")
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_path)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def alert(self, severity, category, source, message, details=None):
        alert = {
            "severity": severity,
            "category": category,
            "source": source,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }
        self.alerts.append(alert)

        # Log to file
        log_msg = f"[{severity}] [{category}] [{source}] {message}"
        if severity == "CRITICAL":
            self.logger.critical(log_msg)
        elif severity == "WARNING":
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)

        # Route to channels
        channels = self.config["severity_routing"].get(severity, ["log_file"])
        for ch in channels:
            if self.config["channels"].get(ch, {}).get("enabled", False):
                self._send(ch, alert)

    def _send(self, channel, alert):
        if channel == "email":
            self._send_email(alert)
        elif channel == "slack_webhook":
            self._send_slack(alert)

    def _send_email(self, alert):
        try:
            cfg = self.config["channels"]["email"]
            msg = MIMEText(
                f"Severity: {alert['severity']}\n"
                f"Category: {alert['category']}\n"
                f"Source: {alert['source']}\n"
                f"Message: {alert['message']}\n"
                f"Time: {alert['timestamp']}\n"
                f"Details: {json.dumps(alert['details'], indent=2)}"
            )
            msg["Subject"] = f"[{alert['severity']}] Morocco Pipeline: {alert['category']}"
            msg["From"] = cfg["sender"]
            msg["To"] = ", ".join(cfg["recipients"])

            with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"]) as server:
                server.starttls()
                server.login(cfg["sender"], cfg["password"])
                server.send_message(msg)
        except Exception as e:
            self.logger.error(f"Email alert failed: {e}")

    def _send_slack(self, alert):
        try:
            import requests
            cfg = self.config["channels"]["slack_webhook"]
            color = {"CRITICAL": "#ff0000", "WARNING": "#ffaa00", "INFO": "#00ff00"}.get(alert["severity"], "#cccccc")
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"[{alert['severity']}] {alert['category']}",
                    "text": alert["message"],
                    "fields": [
                        {"title": "Source", "value": alert["source"], "short": True},
                        {"title": "Time", "value": alert["timestamp"], "short": True},
                    ],
                }]
            }
            requests.post(cfg["webhook_url"], json=payload, timeout=5)
        except Exception as e:
            self.logger.error(f"Slack alert failed: {e}")

    def save_alerts(self):
        path = RESULTS_DIR / f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report = {
            "timestamp": datetime.now().isoformat(),
            "total": len(self.alerts),
            "critical": sum(1 for a in self.alerts if a["severity"] == "CRITICAL"),
            "warnings": sum(1 for a in self.alerts if a["severity"] == "WARNING"),
            "info": sum(1 for a in self.alerts if a["severity"] == "INFO"),
            "alerts": self.alerts,
        }
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Alert report saved: {path}")
        return report


class PipelineMonitor:
    """Monitors pipeline execution and triggers alerts."""

    def __init__(self, alert_manager=None):
        self.am = alert_manager or AlertManager()
        self.start_time = None

    def on_pipeline_start(self, pipeline_name):
        self.start_time = datetime.now()
        self.am.alert("INFO", "PIPELINE", pipeline_name, f"Pipeline started")

    def on_pipeline_end(self, pipeline_name, success=True, stats=None):
        duration = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
        if success:
            self.am.alert("INFO", "PIPELINE", pipeline_name,
                         f"Pipeline completed in {duration:.1f}min",
                         {"duration_minutes": round(duration, 2), "stats": stats})
        else:
            self.am.alert("CRITICAL", "PIPELINE", pipeline_name,
                         f"Pipeline FAILED after {duration:.1f}min",
                         {"duration_minutes": round(duration, 2)})

    def on_stage_start(self, stage_name):
        self.am.alert("INFO", "STAGE", stage_name, f"Stage started")

    def on_stage_end(self, stage_name, success=True, rows_processed=None):
        if success:
            msg = f"Stage completed"
            if rows_processed:
                msg += f" ({rows_processed} rows)"
            self.am.alert("INFO", "STAGE", stage_name, msg,
                         {"rows": rows_processed})
        else:
            self.am.alert("CRITICAL", "STAGE", stage_name, f"Stage FAILED")

    def on_data_check(self, check_name, passed, details=None):
        severity = "INFO" if passed else "WARNING"
        self.am.alert(severity, "DATA_CHECK", check_name,
                     "Check passed" if passed else "Check failed",
                     details)

    def on_anomaly(self, table, column, anomaly_count, total_count):
        pct = anomaly_count / total_count * 100
        severity = "CRITICAL" if pct > 10 else "WARNING"
        self.am.alert(severity, "ANOMALY", table,
                     f"{column}: {anomaly_count}/{total_count} anomalous ({pct:.1f}%)",
                     {"column": column, "count": anomaly_count, "pct": round(pct, 2)})

    def on_schema_change(self, table, missing, added):
        if missing:
            self.am.alert("CRITICAL", "SCHEMA_CHANGE", table,
                         f"Columns removed: {missing}", {"missing": missing})
        if added:
            self.am.alert("WARNING", "SCHEMA_CHANGE", table,
                         f"Columns added: {added}", {"added": added})

    def on_volume_drop(self, table, expected, actual):
        drop_pct = (expected - actual) / expected * 100
        severity = "CRITICAL" if drop_pct > 30 else "WARNING"
        self.am.alert(severity, "VOLUME_DROP", table,
                     f"Volume: {actual} (expected {expected}, -{drop_pct:.1f}%)",
                     {"expected": expected, "actual": actual, "drop_pct": round(drop_pct, 2)})

    def on_null_spike(self, table, column, null_pct):
        severity = "CRITICAL" if null_pct > 20 else "WARNING"
        self.am.alert(severity, "NULL_SPIKE", table,
                     f"{column}: {null_pct:.1f}% nulls",
                     {"column": column, "null_pct": round(null_pct, 2)})

    def save(self):
        return self.am.save_alerts()


if __name__ == "__main__":
    am = AlertManager()
    mon = PipelineMonitor(am)

    # Demo
    mon.on_pipeline_start("morocco-etl")
    mon.on_stage_start("fetch_wb")
    mon.on_stage_end("fetch_wb", success=True, rows_processed=72)
    mon.on_data_check("indicators.not_null", passed=True)
    mon.on_anomaly("indicators_clean", "inflation", 3, 72)
    mon.on_null_spike("bank_prices", "close", 12.5)
    mon.on_pipeline_end("morocco-etl", success=True, stats={"tables": 5, "rows": 350})
    mon.save()
