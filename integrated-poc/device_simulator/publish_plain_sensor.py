from pathlib import Path
import sys
import json
import argparse
import time
import random
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from config import MQTT_HOST, MQTT_PORT, DEFAULT_PLAIN_TOPIC, DEFAULT_SENSOR_ID


def build_simulated_payload(sequence: int) -> dict:
    return {
        "sensor_id": DEFAULT_SENSOR_ID,
        "source": "simulated_sensor",
        "sequence": sequence,
        "temperature": round(random.uniform(22.0, 28.0), 2),
        "humidity": round(random.uniform(45.0, 75.0), 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def publish_message(topic: str, payload: dict):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    message = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    result = client.publish(topic, message, qos=1)

    client.loop(timeout=1.0)
    client.disconnect()

    print("[sensor] publish requested")
    print("topic:", topic)
    print("mqtt_mid:", result.mid)
    print("mqtt_rc:", result.rc)
    print("payload:", message)

def main():
    parser = argparse.ArgumentParser(description="Publish plain sensor data to MQTT.")
    parser.add_argument("--once", action="store_true", help="Publish one message and exit.")
    parser.add_argument("--interval", type=float, default=3.0, help="Interval between messages.")
    args = parser.parse_args()

    sequence = 1

    while True:
        payload = build_simulated_payload(sequence)
        publish_message(DEFAULT_PLAIN_TOPIC, payload)

        if args.once:
            break

        sequence += 1
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
