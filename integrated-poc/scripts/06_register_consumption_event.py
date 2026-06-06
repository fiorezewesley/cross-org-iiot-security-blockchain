from pathlib import Path
import sys
import argparse

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from hash_utils import sha256_text
from config import DEFAULT_SUBSCRIBER_ID, DEFAULT_PROTECTED_TOPIC


def main():
    parser = argparse.ArgumentParser(
        description="Register a simulated consumption/decryption event on-chain."
    )
    parser.add_argument(
        "--success",
        action="store_true",
        help="Mark the simulated consumption event as successful."
    )
    parser.add_argument(
        "--failure",
        action="store_true",
        help="Mark the simulated consumption event as failed."
    )

    args = parser.parse_args()

    if args.success and args.failure:
        raise RuntimeError("Use only --success or --failure, not both.")

    success = True if args.success else False

    client = BlockchainClient()

    print("[PoC] Consumption event registration")
    print("-" * 80)

    if success:
        simulated_result = '{"sensor_id":"sensor_001","temperature":23.7,"humidity":60}'
    else:
        simulated_result = "decryption_failed_due_to_unsatisfied_attributes"

    result_hash = sha256_text(simulated_result)

    print("[1] Simulated consumption result")
    print("success:", success)
    print("result:", simulated_result)
    print("result_hash:", result_hash)
    print("-" * 80)

    receipt = client.store_consumption_event(
        subscriber_id=DEFAULT_SUBSCRIBER_ID,
        topic=DEFAULT_PROTECTED_TOPIC,
        success=success,
        result_hash=result_hash
    )

    print("[2] Consumption event transaction")
    print("tx_hash:", receipt["tx_hash"])
    print("status:", receipt["status"])
    print("block_number:", receipt["block_number"])
    print("gas_used:", receipt["gas_used"])
    print("-" * 80)

    print("[OK] Consumption/decryption event registered on-chain.")


if __name__ == "__main__":
    main()
