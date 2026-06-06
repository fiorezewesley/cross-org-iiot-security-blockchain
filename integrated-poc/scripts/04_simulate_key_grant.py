from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from hash_utils import sha256_text
from config import DEFAULT_AUTHORIZED_ATTRIBUTES


def print_receipt(label: str, receipt: dict):
    print(label)
    print("tx_hash:", receipt["tx_hash"])
    print("status:", receipt["status"])
    print("block_number:", receipt["block_number"])
    print("gas_used:", receipt["gas_used"])
    print("-" * 80)


def main():
    client = BlockchainClient()

    print("[PoC] Simulated ABE key grant")
    print("-" * 80)

    pending_requests = client.get_pending_access_requests()

    print("[1] Pending access requests before grant")
    print(pending_requests)
    print("-" * 80)

    if not pending_requests:
        print("[OK] No pending access requests found.")
        return

    for request in pending_requests:
        request_id = request["request_id"]
        subscriber_id = request["subscriber_id"]
        topic = request["topic"]

        simulated_usk_material = (
            f"simulated_user_secret_key|"
            f"request_id={request_id}|"
            f"subscriber_id={subscriber_id}|"
            f"topic={topic}|"
            f"attributes={DEFAULT_AUTHORIZED_ATTRIBUTES}"
        )

        usk_hash = sha256_text(simulated_usk_material)

        print("[2] Granting simulated ABE user key")
        print("request_id:", request_id)
        print("subscriber_id:", subscriber_id)
        print("topic:", topic)
        print("attributes:", DEFAULT_AUTHORIZED_ATTRIBUTES)
        print("usk_hash:", usk_hash)
        print("-" * 80)

        receipt = client.grant_key(request_id, usk_hash)
        print_receipt("[3] Key grant transaction", receipt)

        print("[4] Grant status")
        print("hasKeyGrant:", client.has_key_grant(request_id))
        print("keyGrant:", client.get_key_grant(request_id))
        print("-" * 80)

    print("[5] Pending access requests after grant")
    print(client.get_pending_access_requests())
    print("-" * 80)

    print("[OK] Simulated ABE key grant metadata registered on-chain.")


if __name__ == "__main__":
    main()
