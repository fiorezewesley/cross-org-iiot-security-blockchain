from pathlib import Path
import sys
import json
import argparse
import time
from typing import Optional

import paho.mqtt.client as mqtt

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from config import (
    MQTT_HOST,
    MQTT_PORT,
    DEFAULT_PLAIN_TOPIC,
    DEFAULT_PROTECTED_TOPIC,
    DEFAULT_ABE_POLICY,
)
from openabe_client import OpenABEClient
from hash_utils import sha256_text
from poc_logger import append_event, append_metric, now_perf, elapsed_ms


received_payload: Optional[dict] = None


def normalize_payload(payload: dict) -> dict:
    required_fields = [
        "sensor_id",
        "source",
        "sequence",
        "temperature",
        "humidity",
        "timestamp_ms",
    ]

    missing = [
        field for field in required_fields
        if field not in payload
    ]

    if missing:
        raise ValueError(f"Missing required fields in MQTT payload: {missing}")

    return payload


def wait_for_mqtt_message(host: str, port: int, topic: str, timeout: int) -> dict:
    global received_payload
    received_payload = None

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("[mqtt_collect] connected to MQTT broker")
            print("broker:", f"{host}:{port}")
            print("subscribing topic:", topic)
            client.subscribe(topic)
        else:
            print("[mqtt_collect][ERROR] MQTT connection failed with rc:", rc)

    def on_message(client, userdata, msg):
        global received_payload

        raw_payload = msg.payload.decode("utf-8", errors="ignore").strip()

        print("[mqtt_collect] message received")
        print("topic:", msg.topic)
        print("payload:", raw_payload)

        try:
            parsed = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            print("[mqtt_collect][WARN] invalid JSON ignored:", exc)
            return

        received_payload = parsed
        client.disconnect()

    client = mqtt.Client(client_id=f"poc_mqtt_collector_{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(host, port, keepalive=60)
    client.loop_start()

    start_time = time.time()

    try:
        while received_payload is None:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"No valid MQTT JSON payload received from topic {topic} "
                    f"within {timeout} seconds."
                )

            time.sleep(0.2)
    finally:
        client.loop_stop()

    return received_payload


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Collects one real ESP32/DHT22 payload from MQTT and encrypts it "
            "with OpenABE as the current ciphertext."
        )
    )

    parser.add_argument("--host", default=MQTT_HOST)
    parser.add_argument("--port", type=int, default=MQTT_PORT)
    parser.add_argument("--plain-topic", default=DEFAULT_PLAIN_TOPIC)
    parser.add_argument("--protected-topic", default=DEFAULT_PROTECTED_TOPIC)
    parser.add_argument("--policy", default=DEFAULT_ABE_POLICY)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--publish-protected",
        action="store_true",
        help="Publishes the generated ciphertext_b64 to the protected MQTT topic.",
    )

    args = parser.parse_args()

    total_start = now_perf()

    print("=" * 80)
    print("[mqtt_collect] Collecting real sensor payload from MQTT")
    print("=" * 80)

    payload = wait_for_mqtt_message(
        host=args.host,
        port=args.port,
        topic=args.plain_topic,
        timeout=args.timeout,
    )

    payload = normalize_payload(payload)

    plaintext = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    plaintext_hash = sha256_text(plaintext)

    print("-" * 80)
    print("[mqtt_collect] normalized payload")
    print(plaintext)
    print("plaintext_hash:", plaintext_hash)
    print("policy:", args.policy)

    abe = OpenABEClient()

    encrypt_start = now_perf()
    encryption_result = abe.encrypt_to_b64(
        plaintext=plaintext,
        policy=args.policy,
    )
    abe_encrypt_ms = elapsed_ms(encrypt_start)

    ciphertext_b64 = encryption_result["ciphertext_b64"]
    ciphertext_hash = sha256_text(ciphertext_b64)
    ciphertext_size = encryption_result["ciphertext_bin_bytes"]

    mqtt_publish_ms = ""

    if args.publish_protected:
        publish_start = now_perf()

        publisher = mqtt.Client(client_id=f"poc_protected_publisher_{int(time.time())}")
        publisher.connect(args.host, args.port, keepalive=60)

        protected_message = json.dumps(
            {
                "sensor_id": payload["sensor_id"],
                "source": payload["source"],
                "sequence": payload["sequence"],
                "plain_topic": args.plain_topic,
                "protected_topic": args.protected_topic,
                "policy": args.policy,
                "ciphertext_b64": ciphertext_b64,
                "ciphertext_hash": ciphertext_hash,
                "ciphertext_bin_bytes": ciphertext_size,
            },
            separators=(",", ":"),
            ensure_ascii=False,
        )

        result = publisher.publish(args.protected_topic, protected_message)
        result.wait_for_publish()
        publisher.disconnect()

        mqtt_publish_ms = elapsed_ms(publish_start)

        print("[mqtt_collect] protected ciphertext published")
        print("protected_topic:", args.protected_topic)
        print("mqtt_publish_ms:", mqtt_publish_ms)

    total_processing_ms = elapsed_ms(total_start)

    print("-" * 80)
    print("[mqtt_collect] OpenABE encryption completed")
    print("abe_encrypt_ms:", abe_encrypt_ms)
    print("ciphertext_bin_bytes:", ciphertext_size)
    print("ciphertext_b64_bytes:", len(ciphertext_b64.encode("utf-8")))
    print("ciphertext_hash:", ciphertext_hash)

    print("STDOUT:")
    print(encryption_result["stdout"])

    print("STDERR:")
    print(encryption_result["stderr"])

    append_event({
        "component": "mqtt_collect",
        "event_type": "real_mqtt_sensor_payload_encrypted",
        "sensor_id": payload.get("sensor_id", ""),
        "source": payload.get("source", ""),
        "sequence": payload.get("sequence", ""),
        "plain_topic": args.plain_topic,
        "protected_topic": args.protected_topic,
        "policy": args.policy,
        "plaintext_hash": plaintext_hash,
        "ciphertext_hash": ciphertext_hash,
        "plaintext": plaintext,
        "ciphertext_bin_bytes": ciphertext_size,
        "ciphertext_b64_bytes": len(ciphertext_b64.encode("utf-8")),
        "abe_encrypt_ms": abe_encrypt_ms,
        "mqtt_publish_ms": mqtt_publish_ms,
        "total_processing_ms": total_processing_ms,
    })

    append_metric({
        "component": "mqtt_collect",
        "event_type": "real_mqtt_sensor_payload_encrypted",
        "sensor_id": payload.get("sensor_id", ""),
        "sequence": payload.get("sequence", ""),
        "plain_topic": args.plain_topic,
        "protected_topic": args.protected_topic,
        "policy": args.policy,
        "success": True,
        "plaintext_bytes": len(plaintext.encode("utf-8")),
        "ciphertext_bin_bytes": ciphertext_size,
        "ciphertext_b64_bytes": len(ciphertext_b64.encode("utf-8")),
        "abe_encrypt_ms": abe_encrypt_ms,
        "mqtt_publish_ms": mqtt_publish_ms,
        "total_processing_ms": total_processing_ms,
        "ciphertext_hash": ciphertext_hash,
        "error": "",
    })

    print("-" * 80)
    print("[OK] Real MQTT sensor payload encrypted and stored as current OpenABE ciphertext.")
    print("[INFO] The next decrypt operation will use this newly generated ciphertext.")


if __name__ == "__main__":
    main()
