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
    TOPIC_PROTECTED_PATTERN,
    DEFAULT_SUBSCRIBER_ID,
    DEFAULT_DECRYPTED_TOPIC,
)


blockchain = BlockchainClient()
abe = OpenABEClient()

def extract_recovered_message(openabe_output: str) -> str:
    marker = "[decrypt] recovered message:"

    if marker in openabe_output:
        return openabe_output.split(marker, 1)[1].strip()

    return openabe_output.strip()



def on_connect(client, userdata, flags, reason_code, properties):
    print("[subscriber_crypto] connected to MQTT")
    print("[subscriber_crypto] subscribing to:", TOPIC_PROTECTED_PATTERN)
    client.subscribe(TOPIC_PROTECTED_PATTERN, qos=1)


def on_message(client, userdata, msg):
    protected_topic = msg.topic

    try:
        protected_json = msg.payload.decode("utf-8")

        print("-" * 80)
        print("[subscriber_crypto] protected message received")
        print("topic:", protected_topic)

        protected_message = json.loads(protected_json)

        ciphertext_b64 = protected_message["ciphertext_b64"]

        print("[subscriber_crypto] decrypting with real OpenABE...")
        openabe_output = abe.decrypt_from_b64(ciphertext_b64)
        recovered = extract_recovered_message(openabe_output)

        result_hash = sha256_text(recovered)

        receipt = blockchain.store_consumption_event(
            subscriber_id=DEFAULT_SUBSCRIBER_ID,
            topic=protected_topic,
            success=True,
            result_hash=result_hash
        )

        print("[subscriber_crypto] decryption success")
        print("recovered:", recovered)
        print("[subscriber_crypto] blockchain receipt:", receipt)

        decrypted_message = {
            "status": "decrypted",
            "subscriber_id": DEFAULT_SUBSCRIBER_ID,
            "protected_topic": protected_topic,
            "result_hash": result_hash,
            "plaintext": recovered,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        decrypted_json = json.dumps(decrypted_message, separators=(",", ":"), sort_keys=True)

        result = client.publish(DEFAULT_DECRYPTED_TOPIC, decrypted_json, qos=1)

        print("[subscriber_crypto] decrypted message publish requested")
        print("decrypted_topic:", DEFAULT_DECRYPTED_TOPIC)
        print("mqtt_mid:", result.mid)
        print("mqtt_rc:", result.rc)

    except Exception as exc:
        error_text = str(exc)
        result_hash = sha256_text(error_text)

        try:
            receipt = blockchain.store_consumption_event(
                subscriber_id=DEFAULT_SUBSCRIBER_ID,
                topic=protected_topic,
                success=False,
                result_hash=result_hash
            )
            print("[subscriber_crypto] failure registered on-chain:", receipt)
        except Exception as chain_exc:
            print("[subscriber_crypto][CHAIN ERROR]", str(chain_exc))

        print("[subscriber_crypto][ERROR]", error_text)


def main():
    print("[subscriber_crypto] starting service")
    print("[subscriber_crypto] MQTT:", MQTT_HOST, MQTT_PORT)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
