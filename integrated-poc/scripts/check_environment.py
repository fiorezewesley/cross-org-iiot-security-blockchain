from pathlib import Path
import sys
import subprocess

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent

sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from config import (
    BESU_RPC_URL,
    CHAIN_ID,
    DEFAULT_PRODUCER_ID,
    DEFAULT_SUBSCRIBER_ID,
    DEFAULT_PROTECTED_TOPIC,
)


OPENABE_CONTAINER = "openabe-lab-split-test"

SUBSCRIBER_PUBLIC_KEY_PATH = (
    BASE_DIR / "runtime" / "keys" / "consumer_001" / "subscriber_ecies_public.pem"
)

SUBSCRIBER_PRIVATE_KEY_PATH = (
    BASE_DIR / "runtime" / "keys" / "consumer_001" / "subscriber_ecies_private.pem"
)


def ok(message: str):
    print(f"[OK] {message}")


def warn(message: str):
    print(f"[WARN] {message}")


def fail(message: str):
    print(f"[FAIL] {message}")


def check_docker_container(container_name: str) -> bool:
    try:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "-f",
                "{{.State.Running}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        return result.stdout.strip() == "true"
    except Exception:
        return False


def main():
    print("=" * 80)
    print("PoC Environment Check")
    print("=" * 80)

    print("[INFO] Project directory:", PROJECT_DIR)
    print("[INFO] Integrated PoC directory:", BASE_DIR)
    print("-" * 80)

    client = BlockchainClient()

    if client.web3.is_connected():
        ok(f"Besu RPC connected: {BESU_RPC_URL}")
    else:
        fail(f"Could not connect to Besu RPC: {BESU_RPC_URL}")
        raise SystemExit(1)

    chain_id = client.web3.eth.chain_id

    if chain_id == CHAIN_ID:
        ok(f"Chain ID: {chain_id}")
    else:
        fail(f"Unexpected Chain ID. Expected {CHAIN_ID}, got {chain_id}")
        raise SystemExit(1)

    ok(f"Contract address loaded: {client.contract_address}")

    functions = sorted([
        item.get("name")
        for item in client.contract.abi
        if item.get("type") == "function" and item.get("name")
    ])

    required_functions = [
        "registerDevice",
        "registerSubscriberAttributes",
        "getSubscriberAttributes",
        "registerTopicPolicy",
        "getTopicPolicy",
        "requestAccess",
        "getPendingAccessRequests",
        "grantEncryptedKey",
        "getKeyGrant",
    ]

    for function_name in required_functions:
        if function_name in functions:
            ok(f"Contract function available: {function_name}")
        else:
            fail(f"Missing contract function: {function_name}")
            raise SystemExit(1)

    try:
        owner = client.contract.functions.owner().call()
        ok(f"Contract owner: {owner}")
    except Exception as exc:
        fail(f"Could not read contract owner: {exc}")
        raise SystemExit(1)

    if check_docker_container(OPENABE_CONTAINER):
        ok(f"OpenABE container running: {OPENABE_CONTAINER}")
    else:
        fail(f"OpenABE container is not running: {OPENABE_CONTAINER}")
        raise SystemExit(1)

    if SUBSCRIBER_PUBLIC_KEY_PATH.exists():
        ok(f"Subscriber ECIES public key found: {SUBSCRIBER_PUBLIC_KEY_PATH}")
    else:
        warn(f"Subscriber ECIES public key not found: {SUBSCRIBER_PUBLIC_KEY_PATH}")
        warn("Run: python3 integrated-poc/scripts/09_generate_subscriber_ecies_keypair.py")

    if SUBSCRIBER_PRIVATE_KEY_PATH.exists():
        ok(f"Subscriber ECIES private key found: {SUBSCRIBER_PRIVATE_KEY_PATH}")
    else:
        warn(f"Subscriber ECIES private key not found: {SUBSCRIBER_PRIVATE_KEY_PATH}")
        warn("Run: python3 integrated-poc/scripts/09_generate_subscriber_ecies_keypair.py")

    print("-" * 80)

    try:
        policy = client.get_topic_policy(DEFAULT_PROTECTED_TOPIC)
        ok(f"Topic policy found for {DEFAULT_PROTECTED_TOPIC}: {policy}")
    except Exception:
        warn(f"Topic policy not found yet for: {DEFAULT_PROTECTED_TOPIC}")
        warn("This is normal before running 02_bootstrap_onchain_state.py")

    try:
        attributes = client.get_subscriber_attributes(DEFAULT_SUBSCRIBER_ID)
        ok(f"Subscriber attributes found for {DEFAULT_SUBSCRIBER_ID}: {attributes}")
    except Exception:
        warn(f"Subscriber attributes not found yet for: {DEFAULT_SUBSCRIBER_ID}")
        warn("This is normal before running 02_bootstrap_onchain_state.py")

    print("-" * 80)
    ok("Environment check completed.")


if __name__ == "__main__":
    main()

