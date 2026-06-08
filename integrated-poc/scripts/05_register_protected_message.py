from pathlib import Path
import sys
import json
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from hash_utils import sha256_text, canonical_json
from config import DEFAULT_PRODUCER_ID, DEFAULT_PROTECTED_TOPIC


def main():
    client = BlockchainClient()

    print("[PoC] Protected message metadata registration")
    print("-" * 80)

    simulated_sensor_payload = {
        "sensor_id": DEFAULT_PRODUCER_ID,
        "temperature": 23.7,
        "humidity": 60,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    plaintext_json = canonical_json(simulated_sensor_payload)

    simulated_ciphertext = json.dumps({
        "scheme": "SIMULATED_ABE",
        "policy": client.get_topic_policy(DEFAULT_PROTECTED_TOPIC),
        "ciphertext": f"encrypted({plaintext_json})"
    }, sort_keys=True)

    ciphertext_hash = sha256_text(simulated_ciphertext)

    print("[1] Simulated plaintext payload")
    print(plaintext_json)
    print("-" * 80)

    print("[2] Simulated protected payload")
    print(simulated_ciphertext)
    print("-" * 80)

    print("[3] Ciphertext hash")
    print(ciphertext_hash)
    print("-" * 80)

    receipt = client.store_protected_message(
        DEFAULT_PRODUCER_ID,
        DEFAULT_PROTECTED_TOPIC,
        ciphertext_hash
    )

    print("[4] Protected message metadata transaction")
    print("tx_hash:", receipt["tx_hash"])
    print("status:", receipt["status"])
    print("block_number:", receipt["block_number"])
    print("gas_used:", receipt["gas_used"])
    print("-" * 80)

    print("[OK] Protected message metadata registered on-chain.")


if __name__ == "__main__":
    main()
