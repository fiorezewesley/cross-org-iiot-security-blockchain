from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from config import DEFAULT_SUBSCRIBER_ID, DEFAULT_PROTECTED_TOPIC


def main():
    client = BlockchainClient()

    print("[PoC] Access request")
    print("-" * 80)

    receipt = client.request_access(
        DEFAULT_SUBSCRIBER_ID,
        DEFAULT_PROTECTED_TOPIC
    )

    print("[1] Access request transaction")
    print("tx_hash:", receipt["tx_hash"])
    print("status:", receipt["status"])
    print("block_number:", receipt["block_number"])
    print("gas_used:", receipt["gas_used"])
    print("-" * 80)

    last_request_id = client.get_last_request_id()

    print("[2] Last request ID")
    print("lastRequestId:", last_request_id)
    print("-" * 80)

    print("[3] Pending access requests")
    pending = client.get_pending_access_requests()
    print(pending)
    print("-" * 80)

    print("[OK] Access request registered on-chain.")


if __name__ == "__main__":
    main()
