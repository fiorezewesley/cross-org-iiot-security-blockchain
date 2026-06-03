import csv
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt


# ============================================================
# Experiment 3 - Message Volume Evaluation with Real Sensor Data
# ============================================================

EXPERIMENT_NAME = "exp3_message_volume_real_sensor"

MQTT_HOST = "localhost"
MQTT_PORT = 1883

INPUT_TOPIC = "sala/sensor"
OUTPUT_TOPIC = "sala/sensor/ciphertext/exp3"

OPENABE_CONTAINER = "openabe-lab-split-test"
LD_PATH = "/openabe/deps/root/lib:/openabe/root/lib:/usr/local/lib:$LD_LIBRARY_PATH"

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

POLICY = "attr1 or attr2"
USK_ATTRIBUTES = "|attr1"

# Ajuste aqui os volumes que deseja testar.
# Como o ESP32 publica aproximadamente a cada 5 segundos,
# 30 mensagens levam cerca de 2,5 minutos;
# 60 mensagens levam cerca de 5 minutos;
# 120 mensagens levam cerca de 10 minutos.
MESSAGE_VOLUMES = [30, 60, 120]

# Tempo máximo de espera para cada grupo, em segundos.
MAX_WAIT_SECONDS_PER_GROUP = 1200


def run_command(cmd, input_text=None):
    result = subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True
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


def normalize_payload(raw_payload):
    parsed = json.loads(raw_payload)
    return json.dumps(parsed, separators=(",", ":"))


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

    mqtt_message = json.dumps(protected_message)
    mqtt_message_compact = json.dumps(protected_message, separators=(",", ":"))

    return protected_message, mqtt_message, mqtt_message_compact


class ExperimentRunner:
    def __init__(self, target_messages):
        self.target_messages = target_messages
        self.rows = []
        self.summary = None
        self.received_count = 0
        self.started_at = None
        self.finished = False

        self.total_plaintext_bytes = 0
        self.total_ciphertext_bin_bytes = 0
        self.total_ciphertext_b64_bytes = 0
        self.total_mqtt_message_bytes = 0
        self.total_mqtt_compact_message_bytes = 0
        self.total_encryption_time_ms = 0.0
        self.total_decryption_time_ms = 0.0
        self.successful_decryptions = 0
        self.failed_decryptions = 0
        self.invalid_messages = 0

    def on_connect(self, client, userdata, flags, rc):
        print(f"[mqtt] connected rc={rc}")
        client.subscribe(INPUT_TOPIC)
        print(f"[mqtt] subscribed to {INPUT_TOPIC}")

    def on_message(self, client, userdata, msg):
        if self.finished:
            return

        try:
            raw_payload = msg.payload.decode("utf-8").strip()
            normalized_payload = normalize_payload(raw_payload)

            self.received_count += 1
            message_index = self.received_count

            print(f"[message] {message_index}/{self.target_messages}: {normalized_payload}")

            plaintext_bytes = len(normalized_payload.encode("utf-8"))

            encryption_time_ms, encrypt_stdout, encrypt_stderr = encrypt_payload(normalized_payload)

            ciphertext_b64, ciphertext_bin_bytes, ciphertext_b64_bytes = read_ciphertext_from_container()

            protected_message, mqtt_message, mqtt_message_compact = build_mqtt_message(ciphertext_b64)

            mqtt_message_bytes = len(mqtt_message.encode("utf-8"))
            mqtt_compact_message_bytes = len(mqtt_message_compact.encode("utf-8"))

            # Publish protected message to a dedicated experiment topic.
            client.publish(OUTPUT_TOPIC, mqtt_message)

            decryption_time_ms, decrypt_stdout, decrypt_stderr = decrypt_current_ciphertext()

            decrypt_success = normalized_payload in decrypt_stdout

            if decrypt_success:
                self.successful_decryptions += 1
            else:
                self.failed_decryptions += 1

            overhead_ciphertext_ratio = ciphertext_bin_bytes / plaintext_bytes
            overhead_mqtt_ratio = mqtt_message_bytes / plaintext_bytes
            overhead_mqtt_percentage = ((mqtt_message_bytes - plaintext_bytes) / plaintext_bytes) * 100

            self.total_plaintext_bytes += plaintext_bytes
            self.total_ciphertext_bin_bytes += ciphertext_bin_bytes
            self.total_ciphertext_b64_bytes += ciphertext_b64_bytes
            self.total_mqtt_message_bytes += mqtt_message_bytes
            self.total_mqtt_compact_message_bytes += mqtt_compact_message_bytes
            self.total_encryption_time_ms += encryption_time_ms
            self.total_decryption_time_ms += decryption_time_ms

            row = {
                "experiment": EXPERIMENT_NAME,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "target_message_volume": self.target_messages,
                "message_index": message_index,
                "input_topic": INPUT_TOPIC,
                "output_topic": OUTPUT_TOPIC,
                "raw_payload": raw_payload,
                "normalized_payload": normalized_payload,
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

            self.rows.append(row)

            if self.received_count >= self.target_messages:
                elapsed_s = time.perf_counter() - self.started_at

                self.summary = {
                    "experiment": EXPERIMENT_NAME,
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "target_message_volume": self.target_messages,
                    "collected_messages": self.received_count,
                    "successful_decryptions": self.successful_decryptions,
                    "failed_decryptions": self.failed_decryptions,
                    "invalid_messages": self.invalid_messages,
                    "policy": POLICY,
                    "usk_attributes": USK_ATTRIBUTES,
                    "total_plaintext_bytes": self.total_plaintext_bytes,
                    "total_ciphertext_bin_bytes": self.total_ciphertext_bin_bytes,
                    "total_ciphertext_b64_bytes": self.total_ciphertext_b64_bytes,
                    "total_mqtt_message_bytes": self.total_mqtt_message_bytes,
                    "total_mqtt_compact_message_bytes": self.total_mqtt_compact_message_bytes,
                    "accumulated_ciphertext_overhead_ratio": round(self.total_ciphertext_bin_bytes / self.total_plaintext_bytes, 4),
                    "accumulated_mqtt_overhead_ratio": round(self.total_mqtt_message_bytes / self.total_plaintext_bytes, 4),
                    "accumulated_mqtt_overhead_percentage": round(((self.total_mqtt_message_bytes - self.total_plaintext_bytes) / self.total_plaintext_bytes) * 100, 2),
                    "total_encryption_time_ms": round(self.total_encryption_time_ms, 3),
                    "total_decryption_time_ms": round(self.total_decryption_time_ms, 3),
                    "average_encryption_time_ms": round(self.total_encryption_time_ms / self.received_count, 3),
                    "average_decryption_time_ms": round(self.total_decryption_time_ms / self.received_count, 3),
                    "elapsed_collection_time_s": round(elapsed_s, 3),
                    "effective_messages_per_second": round(self.received_count / elapsed_s, 4),
                    "average_plaintext_bytes": round(self.total_plaintext_bytes / self.received_count, 3),
                    "average_mqtt_message_bytes": round(self.total_mqtt_message_bytes / self.received_count, 3)
                }

                self.finished = True
                client.disconnect()

        except Exception as e:
            self.invalid_messages += 1
            print(f"[error] invalid or failed message: {e}")

    def run(self):
        self.started_at = time.perf_counter()

        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        client.connect(MQTT_HOST, MQTT_PORT, 60)

        timeout_at = time.perf_counter() + MAX_WAIT_SECONDS_PER_GROUP

        while not self.finished and time.perf_counter() < timeout_at:
            client.loop(timeout=1.0)

        if not self.finished:
            client.disconnect()
            raise TimeoutError(
                f"Experiment timed out before collecting {self.target_messages} messages. "
                f"Collected: {self.received_count}"
            )

        return self.rows, self.summary


def write_csv(output_file, fieldnames, rows):
    with output_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_experiment():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    detail_output_file = RESULTS_DIR / f"{EXPERIMENT_NAME}_details_{timestamp}.csv"
    summary_output_file = RESULTS_DIR / f"{EXPERIMENT_NAME}_summary_{timestamp}.csv"

    print("[experiment] Message Volume Evaluation with Real Sensor Payloads")
    print(f"[experiment] input topic: {INPUT_TOPIC}")
    print(f"[experiment] output topic: {OUTPUT_TOPIC}")
    print(f"[experiment] policy: {POLICY}")
    print(f"[experiment] USK attributes: {USK_ATTRIBUTES}")
    print(f"[experiment] message volumes: {MESSAGE_VOLUMES}")

    initialize_abe_environment()

    all_rows = []
    summary_rows = []

    detail_fieldnames = [
        "experiment",
        "timestamp",
        "target_message_volume",
        "message_index",
        "input_topic",
        "output_topic",
        "raw_payload",
        "normalized_payload",
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

    summary_fieldnames = [
        "experiment",
        "timestamp",
        "target_message_volume",
        "collected_messages",
        "successful_decryptions",
        "failed_decryptions",
        "invalid_messages",
        "policy",
        "usk_attributes",
        "total_plaintext_bytes",
        "total_ciphertext_bin_bytes",
        "total_ciphertext_b64_bytes",
        "total_mqtt_message_bytes",
        "total_mqtt_compact_message_bytes",
        "accumulated_ciphertext_overhead_ratio",
        "accumulated_mqtt_overhead_ratio",
        "accumulated_mqtt_overhead_percentage",
        "total_encryption_time_ms",
        "total_decryption_time_ms",
        "average_encryption_time_ms",
        "average_decryption_time_ms",
        "elapsed_collection_time_s",
        "effective_messages_per_second",
        "average_plaintext_bytes",
        "average_mqtt_message_bytes"
    ]

    for volume in MESSAGE_VOLUMES:
        print("\n" + "=" * 80)
        print(f"[volume] collecting {volume} real sensor messages")
        print("=" * 80)

        runner = ExperimentRunner(target_messages=volume)
        rows, summary = runner.run()

        all_rows.extend(rows)
        summary_rows.append(summary)

        print(f"[volume] completed: {volume} messages")
        print(f"[volume] success: {summary['successful_decryptions']}")
        print(f"[volume] failed: {summary['failed_decryptions']}")
        print(f"[volume] accumulated MQTT overhead: {summary['accumulated_mqtt_overhead_percentage']}%")

    write_csv(detail_output_file, detail_fieldnames, all_rows)
    write_csv(summary_output_file, summary_fieldnames, summary_rows)

    print("\n" + "=" * 80)
    print(f"[done] detail CSV generated: {detail_output_file}")
    print(f"[done] summary CSV generated: {summary_output_file}")


if __name__ == "__main__":
    run_experiment()