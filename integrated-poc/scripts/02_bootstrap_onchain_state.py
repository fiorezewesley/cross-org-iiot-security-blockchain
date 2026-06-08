from pathlib import Path
import sys
import argparse

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from config import (
    DEFAULT_PRODUCER_ID,
    DEFAULT_SUBSCRIBER_ID,
    DEFAULT_PROTECTED_TOPIC,
    DEFAULT_ABE_POLICY,
    DEFAULT_AUTHORIZED_ATTRIBUTES,
)


def print_receipt(label: str, receipt: dict):
    print(label)
    print("tx_hash:", receipt["tx_hash"])
    print("status:", receipt["status"])
    print("block_number:", receipt["block_number"])
    print("gas_used:", receipt["gas_used"])
    print("-" * 80)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Bootstraps the on-chain state for the integrated PoC. "
            "It registers producer, subscriber, subscriber attributes and topic policy."
        )
    )

    parser.add_argument(
        "--subscriber-attributes",
        default=DEFAULT_AUTHORIZED_ATTRIBUTES,
        help=(
            "Attributes assigned to the subscriber. "
            "Example for authorized scenario: '|attr1'. "
            "Example for unauthorized scenario: '|attr3'."
        ),
    )

    parser.add_argument(
        "--policy",
        default=DEFAULT_ABE_POLICY,
        help="ABE policy associated with the protected topic. Example: 'attr1 or attr2'.",
    )

    args = parser.parse_args()

    client = BlockchainClient()

    print("[PoC] Bootstrap on-chain state")
    print("-" * 80)
    print("producer_id:", DEFAULT_PRODUCER_ID)
    print("subscriber_id:", DEFAULT_SUBSCRIBER_ID)
    print("protected_topic:", DEFAULT_PROTECTED_TOPIC)
    print("subscriber_attributes:", args.subscriber_attributes)
    print("topic_policy:", args.policy)
    print("-" * 80)

    receipt = client.register_device(
        DEFAULT_PRODUCER_ID,
        "CompanyA",
        "producer",
    )
    print_receipt("[1] Producer device registered", receipt)

    receipt = client.register_device(
        DEFAULT_SUBSCRIBER_ID,
        "CompanyB",
        "subscriber",
    )
    print_receipt("[2] Subscriber device registered", receipt)

    receipt = client.register_subscriber_attributes(
        DEFAULT_SUBSCRIBER_ID,
        args.subscriber_attributes,
    )
    print_receipt("[3] Subscriber attributes registered", receipt)

    receipt = client.register_topic_policy(
        DEFAULT_PROTECTED_TOPIC,
        args.policy,
    )
    print_receipt("[4] Topic policy registered", receipt)

    policy = client.get_topic_policy(DEFAULT_PROTECTED_TOPIC)
    attributes = client.get_subscriber_attributes(DEFAULT_SUBSCRIBER_ID)

    print("[5] Policy and attributes read from blockchain")
    print("topic:", DEFAULT_PROTECTED_TOPIC)
    print("policy:", policy)
    print("subscriber:", DEFAULT_SUBSCRIBER_ID)
    print("attributes:", attributes)
    print("-" * 80)

    if policy != args.policy:
        raise RuntimeError(
            f"Unexpected policy. Expected '{args.policy}', got '{policy}'."
        )

    if attributes != args.subscriber_attributes:
        raise RuntimeError(
            f"Unexpected attributes. Expected '{args.subscriber_attributes}', got '{attributes}'."
        )

    print("[OK] On-chain devices, subscriber attributes and topic policy are ready.")


if __name__ == "__main__":
    main()