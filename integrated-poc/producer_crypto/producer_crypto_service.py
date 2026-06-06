from pathlib import Path
import sys
import json
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from openabe_client import OpenABEClient
from hash_utils import sha256_text
from config import (
    MQTT_HOST,
    MQTT_PORT,
    TOPIC_PLAIN_PATTERN,
    DEFAULT_PRODUCER_ID,
    DEFAULT_PROTECTED_TOPIC,
)


blockchain = BlockchainClient()
abe = OpenABEClient()


def on_connect(client, userdata, flags, reason_code, properties):
    print("[producer_crypto] connected to MQTT")
    print("[producer_crypto] subscribing to:", TOPIC_PLAIN_PATTERN)
    client.subscribe(TOPIC_PLAIN_PATTERN, qos=1)


def on_message(client, userdata, msg):
    try:
        plain_topic = msg.topic
        plaintext = msg.payload.decode("utf-8")

        print("-" * 80)
        print("[producer_crypto] plain message received")
        print("plain_topic:", plain_topic)
        print("plaintext:", plaintext)

        policy = blockchain.get_topic_policy(DEFAULT_PROTECTED_TOPIC)

        print("[producer_crypto] policy from blockchain:", policy)

        encrypted = abe.encrypt_to_b64(plaintext, policy)
        ciphertext_b64 = encrypted["ciphertext_b64"]

        protected_message = {
            "status": "encrypted",
            "scheme": "CP-ABE/OpenABE",
            "producer_id": DEFAULT_PRODUCER_ID,
            "plain_topic": plain_topic,
            "protected_topic": DEFAULT_PROTECTED_TOPIC,
            "policy": policy,
            "ciphertext_b64": ciphertext_b64,
            "ciphertext_bin_bytes": encrypted["ciphertext_bin_bytes"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        protected_json = json.dumps(protected_message, separators=(",", ":"), sort_keys=True)
        ciphertext_hash = sha256_text(protected_json)

        print("[producer_crypto] ciphertext hash:", ciphertext_hash)

        receipt = blockchain.store_protected_message(
            DEFAULT_PRODUCER_ID,
            DEFAULT_PROTECTED_TOPIC,
            ciphertext_hash
        )

        print("[producer_crypto] blockchain receipt:", receipt)

        result = client.publish(DEFAULT_PROTECTED_TOPIC, protected_json, qos=1)

        print("[producer_crypto] protected message publish requested")
        print("protected_topic:", DEFAULT_PROTECTED_TOPIC)
        print("mqtt_mid:", result.mid)
        print("mqtt_rc:", result.rc)

    except Exception as exc:
        print("[producer_crypto][ERROR]", str(exc))


def main():
    print("[producer_crypto] starting service")
    print("[producer_crypto] MQTT:", MQTT_HOST, MQTT_PORT)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
