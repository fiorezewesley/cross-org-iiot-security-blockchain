import base64
import csv
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

OPENABE_CONTAINER = "openabe-lab-split-test"
LD_PATH = "/openabe/deps/root/lib:/openabe/root/lib:/usr/local/lib:$LD_LIBRARY_PATH"

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

POLICY = "attr1 or attr2"
USK_ATTRIBUTES = "|attr1"

RUNS_PER_SIZE = 10

PAYLOAD_SIZES = [
    32,
    64,
    128,
    256,
    512,
    1024,
    2048,
    4096
]

SENSOR_BASELINE_PAYLOAD = {
    "temp": 24.90,
    "hum": 77.10
}


def run_command(cmd, env=None, input_text=None):
    result = subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        env=env
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed:\n{' '.join(cmd)}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    return result.stdout.strip(), result.stderr.strip()


def docker_exec_bash(command, env_vars=None, input_text=None):
    cmd = ["docker", "exec"]

    if env_vars:
        for key, value in env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])

    if input_text is not None:
        cmd.append("-i")

    cmd.extend([
        OPENABE_CONTAINER,
        "bash",
        "-lc",
        command
    ])

    return run_command(cmd, input_text=input_text)


def initialize_abe_environment():
    print("[setup] generating CP-ABE parameters...")

    docker_exec_bash(
        f"cd /openabe/examples && "
        f"export LD_LIBRARY_PATH={LD_PATH} && "
        f"./cpabe_split setup"
    )

    print(f"[keygen] generating USK with attributes: {USK_ATTRIBUTES}")

    docker_exec_bash(
        f"cd /openabe/examples && "
        f"export LD_LIBRARY_PATH={LD_PATH} && "
        f"./cpabe_split keygen",
        env_vars={
            "OPENABE_ATTRS": USK_ATTRIBUTES
        }
    )


def make_exact_json_payload(target_bytes):
    """
    Creates a valid JSON payload with approximately industrial telemetry structure,
    adjusted to exactly match the target byte size when encoded in UTF-8.
    """

    base = {
        "device": "esp32",
        "sensor": "dht22",
        "seq": 1,
        "data": ""
    }

    base_json = json.dumps(base, separators=(",", ":"))
    base_size = len(base_json.encode("utf-8"))

    if target_bytes < base_size:
        minimal = {"d": ""}
        minimal_json = json.dumps(minimal, separators=(",", ":"))
        filler_len = target_bytes - len(minimal_json.encode("utf-8"))

        if filler_len < 0:
            raise ValueError(f"Target size {target_bytes} is too small for valid JSON.")

        minimal["d"] = "x" * filler_len
        return json.dumps(minimal, separators=(",", ":"))

    filler_len = target_bytes - base_size
    base["data"] = "x" * filler_len

    payload = json.dumps(base, separators=(",", ":"))

    while len(payload.encode("utf-8")) < target_bytes:
        base["data"] += "x"
        payload = json.dumps(base, separators=(",", ":"))

    while len(payload.encode("utf-8")) > target_bytes:
        base["data"] = base["data"][:-1]
        payload = json.dumps(base, separators=(",", ":"))

    return payload


def encrypt_payload(payload):
    start = time.perf_counter()

    stdout, stderr = docker_exec_bash(
        f"cd /openabe/examples && "
        f"export LD_LIBRARY_PATH={LD_PATH} && "
        f"./cpabe_split encrypt",
        env_vars={
            "OPENABE_MSG": payload,
            "OPENABE_POLICY": POLICY
        }
    )

    end = time.perf_counter()

    encryption_time_ms = (end - start) * 1000

    return encryption_time_ms, stdout, stderr


def read_ciphertext_from_container():
    ciphertext_b64, _ = docker_exec_bash(
        "base64 -w 0 /openabe/examples/state/ciphertext.bin"
    )

    ciphertext_bin_size, _ = docker_exec_bash(
        "stat -c%s /openabe/examples/state/ciphertext.bin"
    )

    ciphertext_bin_size = int(ciphertext_bin_size)
    ciphertext_b64_size = len(ciphertext_b64.encode("utf-8"))

    return ciphertext_b64, ciphertext_bin_size, ciphertext_b64_size


def decrypt_current_ciphertext():
    start = time.perf_counter()

    stdout, stderr = docker_exec_bash(
        f"cd /openabe/examples && "
        f"export LD_LIBRARY_PATH={LD_PATH} && "
        f"./cpabe_split decrypt"
    )

    end = time.perf_counter()

    decryption_time_ms = (end - start) * 1000

    return decryption_time_ms, stdout, stderr


def build_mqtt_message(ciphertext_b64):
    protected_message = {
        "status": "encrypted",
        "policy": POLICY,
        "ciphertext_b64": ciphertext_b64
    }

    # Same style as the current producer script: json.dumps with default separators.
    mqtt_message = json.dumps(protected_message)

    # More compact version, useful for comparison.
    mqtt_message_compact = json.dumps(protected_message, separators=(",", ":"))

    return mqtt_message, mqtt_message_compact


def run_experiment():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"exp1_overhead_payload_size_{timestamp}.csv"

    initialize_abe_environment()

    fieldnames = [
        "experiment",
        "timestamp",
        "run",
        "payload_label",
        "payload_target_bytes",
        "plaintext_bytes",
        "policy",
        "usk_attributes",
        "ciphertext_bin_bytes",
        "ciphertext_b64_bytes",
        "mqtt_message_bytes",
        "mqtt_compact_message_bytes",
        "overhead_ciphertext_ratio",
        "overhead_mqtt_ratio",
        "overhead_mqtt_percentage",
        "encryption_time_ms",
        "decryption_time_ms",
        "decrypt_success",
        "recovered_output"
    ]

    rows = []

    payloads = []

    sensor_payload = json.dumps(SENSOR_BASELINE_PAYLOAD, separators=(",", ":"))
    payloads.append(("sensor_baseline", len(sensor_payload.encode("utf-8")), sensor_payload))

    for size in PAYLOAD_SIZES:
        payloads.append((f"payload_{size}_bytes", size, make_exact_json_payload(size)))

    for payload_label, target_size, payload in payloads:
        plaintext_bytes = len(payload.encode("utf-8"))

        print(f"\n[experiment] payload={payload_label} plaintext_bytes={plaintext_bytes}")

        for run in range(1, RUNS_PER_SIZE + 1):
            print(f"[run] {run}/{RUNS_PER_SIZE}")

            encryption_time_ms, encrypt_stdout, encrypt_stderr = encrypt_payload(payload)

            ciphertext_b64, ciphertext_bin_bytes, ciphertext_b64_bytes = read_ciphertext_from_container()

            mqtt_message, mqtt_message_compact = build_mqtt_message(ciphertext_b64)

            mqtt_message_bytes = len(mqtt_message.encode("utf-8"))
            mqtt_compact_message_bytes = len(mqtt_message_compact.encode("utf-8"))

            decryption_time_ms, decrypt_stdout, decrypt_stderr = decrypt_current_ciphertext()

            decrypt_success = payload in decrypt_stdout

            overhead_ciphertext_ratio = ciphertext_bin_bytes / plaintext_bytes
            overhead_mqtt_ratio = mqtt_message_bytes / plaintext_bytes
            overhead_mqtt_percentage = ((mqtt_message_bytes - plaintext_bytes) / plaintext_bytes) * 100

            row = {
                "experiment": "exp1_overhead_payload_size",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "run": run,
                "payload_label": payload_label,
                "payload_target_bytes": target_size,
                "plaintext_bytes": plaintext_bytes,
                "policy": POLICY,
                "usk_attributes": USK_ATTRIBUTES,
                "ciphertext_bin_bytes": ciphertext_bin_bytes,
                "ciphertext_b64_bytes": ciphertext_b64_bytes,
                "mqtt_message_bytes": mqtt_message_bytes,
                "mqtt_compact_message_bytes": mqtt_compact_message_bytes,
                "overhead_ciphertext_ratio": round(overhead_ciphertext_ratio, 4),
                "overhead_mqtt_ratio": round(overhead_mqtt_ratio, 4),
                "overhead_mqtt_percentage": round(overhead_mqtt_percentage, 2),
                "encryption_time_ms": round(encryption_time_ms, 3),
                "decryption_time_ms": round(decryption_time_ms, 3),
                "decrypt_success": decrypt_success,
                "recovered_output": decrypt_stdout.replace("\n", " | ")
            }

            rows.append(row)

    with output_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[done] CSV generated: {output_file}")


if __name__ == "__main__":
    run_experiment()