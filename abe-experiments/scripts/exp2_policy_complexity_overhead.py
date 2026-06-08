import csv
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

OPENABE_CONTAINER = "openabe-lab-split-test"
LD_PATH = "/openabe/deps/root/lib:/openabe/root/lib:/usr/local/lib:$LD_LIBRARY_PATH"

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

EXPERIMENT_NAME = "exp2_policy_complexity_overhead"

# Payload fixo para isolar o impacto da política.
FIXED_PAYLOAD_SIZE_BYTES = 256

# Número de execuções por política.
RUNS_PER_POLICY = 10

# Quantidade de atributos na política.
# Comece com estes valores. Se tudo funcionar bem, depois podemos expandir para 30, 40 e 50.
ATTRIBUTE_COUNTS = [1, 2, 3, 4, 5, 10, 15, 20]

# Tipo de política principal deste experimento.
# AND é mais adequado para representar aumento progressivo de restrição.
POLICY_OPERATOR = "and"


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


def make_exact_json_payload(target_bytes):
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


def build_policy(attribute_count, operator):
    attrs = [f"attr{i}" for i in range(1, attribute_count + 1)]

    if attribute_count == 1:
        return attrs[0]

    separator = f" {operator} "
    return separator.join(attrs)


def build_usk_attributes(attribute_count):
    attrs = [f"attr{i}" for i in range(1, attribute_count + 1)]
    return "|" + "|".join(attrs)


def initialize_setup():
    print("[setup] generating CP-ABE public and secret parameters...")

    docker_exec_bash(
        f"cd /openabe/examples && "
        f"export LD_LIBRARY_PATH={LD_PATH} && "
        f"./cpabe_split setup"
    )


def generate_user_key(usk_attributes):
    stdout, stderr = docker_exec_bash(
        f"cd /openabe/examples && "
        f"export LD_LIBRARY_PATH={LD_PATH} && "
        f"./cpabe_split keygen",
        env_vars={
            "OPENABE_ATTRS": usk_attributes
        }
    )

    return stdout, stderr


def encrypt_payload(payload, policy):
    start = time.perf_counter()

    stdout, stderr = docker_exec_bash(
        f"cd /openabe/examples && "
        f"export LD_LIBRARY_PATH={LD_PATH} && "
        f"./cpabe_split encrypt",
        env_vars={
            "OPENABE_MSG": payload,
            "OPENABE_POLICY": policy
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


def build_mqtt_message(ciphertext_b64, policy):
    protected_message = {
        "status": "encrypted",
        "policy": policy,
        "ciphertext_b64": ciphertext_b64
    }

    mqtt_message = json.dumps(protected_message)
    mqtt_message_compact = json.dumps(protected_message, separators=(",", ":"))

    return mqtt_message, mqtt_message_compact


def run_experiment():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"{EXPERIMENT_NAME}_{timestamp}.csv"

    payload = make_exact_json_payload(FIXED_PAYLOAD_SIZE_BYTES)
    plaintext_bytes = len(payload.encode("utf-8"))

    print(f"[experiment] fixed plaintext size: {plaintext_bytes} bytes")
    print(f"[experiment] policy operator: {POLICY_OPERATOR}")
    print(f"[experiment] runs per policy: {RUNS_PER_POLICY}")

    initialize_setup()

    fieldnames = [
        "experiment",
        "timestamp",
        "run",
        "policy_operator",
        "attribute_count",
        "policy",
        "usk_attributes",
        "plaintext_bytes",
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

    for attribute_count in ATTRIBUTE_COUNTS:
        policy = build_policy(attribute_count, POLICY_OPERATOR)
        usk_attributes = build_usk_attributes(attribute_count)

        print("\n" + "=" * 80)
        print(f"[policy] attribute_count={attribute_count}")
        print(f"[policy] {policy}")
        print(f"[usk] {usk_attributes}")

        print("[keygen] generating compatible USK...")
        generate_user_key(usk_attributes)

        for run in range(1, RUNS_PER_POLICY + 1):
            print(f"[run] {run}/{RUNS_PER_POLICY}")

            encryption_time_ms, encrypt_stdout, encrypt_stderr = encrypt_payload(payload, policy)

            ciphertext_b64, ciphertext_bin_bytes, ciphertext_b64_bytes = read_ciphertext_from_container()

            mqtt_message, mqtt_message_compact = build_mqtt_message(ciphertext_b64, policy)

            mqtt_message_bytes = len(mqtt_message.encode("utf-8"))
            mqtt_compact_message_bytes = len(mqtt_message_compact.encode("utf-8"))

            decryption_time_ms, decrypt_stdout, decrypt_stderr = decrypt_current_ciphertext()

            decrypt_success = payload in decrypt_stdout

            overhead_ciphertext_ratio = ciphertext_bin_bytes / plaintext_bytes
            overhead_mqtt_ratio = mqtt_message_bytes / plaintext_bytes
            overhead_mqtt_percentage = ((mqtt_message_bytes - plaintext_bytes) / plaintext_bytes) * 100

            row = {
                "experiment": EXPERIMENT_NAME,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "run": run,
                "policy_operator": POLICY_OPERATOR,
                "attribute_count": attribute_count,
                "policy": policy,
                "usk_attributes": usk_attributes,
                "plaintext_bytes": plaintext_bytes,
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

    print("\n" + "=" * 80)
    print(f"[done] CSV generated: {output_file}")


if __name__ == "__main__":
    run_experiment()