from pathlib import Path
from datetime import datetime, timezone
import csv
import json
import time
from typing import Dict, Any, Optional


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"

EVENTS_PATH = RESULTS_DIR / "events.jsonl"
METRICS_PATH = RESULTS_DIR / "metrics.csv"


METRICS_FIELDS = [
    "timestamp_utc",
    "component",
    "event_type",
    "message_id",
    "sensor_id",
    "sequence",
    "plain_topic",
    "protected_topic",
    "decrypted_topic",
    "policy",
    "success",
    "plaintext_bytes",
    "ciphertext_bin_bytes",
    "ciphertext_b64_bytes",
    "abe_encrypt_ms",
    "abe_decrypt_ms",
    "blockchain_store_protected_ms",
    "blockchain_store_consumption_ms",
    "mqtt_publish_ms",
    "total_processing_ms",
    "ciphertext_hash",
    "result_hash",
    "tx_hash",
    "block_number",
    "gas_used",
    "error",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_perf() -> float:
    return time.perf_counter()


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def ensure_results_dir():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def append_event(event: Dict[str, Any]):
    """
    Saves a structured event as JSON Lines.
    One line = one JSON event.
    """
    ensure_results_dir()

    event = {
        "timestamp_utc": utc_now_iso(),
        **event,
    }

    with EVENTS_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def append_metric(metric: Dict[str, Any]):
    """
    Saves one metrics row as CSV.
    Missing fields are stored as empty strings.
    """
    ensure_results_dir()

    file_exists = METRICS_PATH.exists()

    row = {field: metric.get(field, "") for field in METRICS_FIELDS}

    if not row["timestamp_utc"]:
        row["timestamp_utc"] = utc_now_iso()

    with METRICS_PATH.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=METRICS_FIELDS)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def build_message_id(sensor_id: str, sequence: Optional[Any]) -> str:
    """
    Creates a stable local message identifier for correlating logs.
    """
    if sequence is None or sequence == "":
        return f"{sensor_id}:unknown:{int(time.time() * 1000)}"

    return f"{sensor_id}:{sequence}"


def safe_get(payload: Dict[str, Any], key: str, default: Any = "") -> Any:
    value = payload.get(key, default)

    if value is None:
        return default

    return value
