from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from config import (
    DEFAULT_PRODUCER_ID,
    DEFAULT_SUBSCRIBER_ID,
    DEFAULT_PROTECTED_TOPIC,
    DEFAULT_ABE_POLICY,
)


def print_receipt(label: str, receipt: dict):
    print(label)
    print("tx_hash:", receipt["tx_hash"])
    print("status:", receipt["status"])
    print("block_number:", receipt["block_number"])
    print("gas_used:", receipt["gas_used"])
    print("-" * 80)


def main():
    client = BlockchainClient()

    print("[PoC] Bootstrap on-chain state")
    print("-" * 80)

    receipt = client.register_device(
        DEFAULT_PRODUCER_ID,
        "CompanyA",
        "producer"
    )
    print_receipt("[1] Producer device registered", receipt)

    receipt = client.register_device(
        DEFAULT_SUBSCRIBER_ID,
        "CompanyB",
        "subscriber"
    )
    print_receipt("[2] Subscriber device registered", receipt)

    receipt = client.register_topic_policy(
        DEFAULT_PROTECTED_TOPIC,
        DEFAULT_ABE_POLICY
    )
    print_receipt("[3] Topic policy registered", receipt)

    policy = client.get_topic_policy(DEFAULT_PROTECTED_TOPIC)

    print("[4] Policy read from blockchain")
    print("topic:", DEFAULT_PROTECTED_TOPIC)
    print("policy:", policy)
    print("-" * 80)

    if policy != DEFAULT_ABE_POLICY:
        raise RuntimeError(
            f"Unexpected policy. Expected '{DEFAULT_ABE_POLICY}', got '{policy}'."
        )

    print("[OK] On-chain devices and topic policy are ready.")


if __name__ == "__main__":
    main()

