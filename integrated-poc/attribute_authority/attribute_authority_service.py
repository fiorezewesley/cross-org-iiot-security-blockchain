from pathlib import Path
import sys
import time
import argparse
from typing import List

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from openabe_client import OpenABEClient
from hash_utils import sha256_text
from poc_logger import append_event, append_metric, elapsed_ms, now_perf
from config import DEFAULT_AUTHORIZED_ATTRIBUTES


blockchain = BlockchainClient()
abe = OpenABEClient()


def normalize_attributes(attributes: str) -> List[str]:
    """
    Converts OpenABE-style attributes into a Python list.

    Example:
        '|attr1|attr2' -> ['attr1', 'attr2']
    """
    if not attributes:
        return []

    return [
        item.strip()
        for item in attributes.replace(",", "|").split("|")
        if item.strip()
    ]


def policy_is_satisfied(policy: str, attributes: str) -> bool:
    """
    Minimal evaluator for simple policies used in this PoC.

    Supported examples:
        attr1 or attr2
        attr1 and attr2

    This does not replace the cryptographic enforcement performed by ABE.
    It only represents the Attribute Authority's decision before generating
    a user key.
    """
    policy_normalized = policy.lower().strip()
    attrs = [attr.lower() for attr in normalize_attributes(attributes)]

    if not policy_normalized:
        return False

    if " or " in policy_normalized:
        required = [
            item.strip()
            for item in policy_normalized.split(" or ")
            if item.strip()
        ]
        return any(item in attrs for item in required)

    if " and " in policy_normalized:
        required = [
            item.strip()
            for item in policy_normalized.split(" and ")
            if item.strip()
        ]
        return all(item in attrs for item in required)

    return policy_normalized in attrs


def build_key_hash(
    request_id: int,
    subscriber_id: str,
    topic: str,
    policy: str,
    attributes: str,
    keygen_stdout: str,
    keygen_stderr: str,
) -> str:
    """
    Creates a deterministic evidence hash for the key grant.

    The actual OpenABE user secret key remains inside the OpenABE environment.
    The blockchain stores only a hash/evidence reference.
    """
    material = (
        f"request_id={request_id}|"
        f"subscriber_id={subscriber_id}|"
        f"topic={topic}|"
        f"policy={policy}|"
        f"attributes={attributes}|"
        f"keygen_stdout={keygen_stdout}|"
        f"keygen_stderr={keygen_stderr}"
    )

    return sha256_text(material)


def process_request(request: dict, attributes: str):
    total_start = now_perf()

    request_id = request["request_id"]
    subscriber_id = request["subscriber_id"]
    topic = request["topic"]

    print("-" * 80)
    print("[attribute_authority] processing access request")
    print("request_id:", request_id)
    print("subscriber_id:", subscriber_id)
    print("topic:", topic)
    print("attributes:", attributes)

    append_event({
        "component": "attribute_authority",
        "event_type": "access_request_detected",
        "request_id": request_id,
        "subscriber_id": subscriber_id,
        "topic": topic,
        "attributes": attributes,
    })

    policy = blockchain.get_topic_policy(topic)

    print("[attribute_authority] policy:", policy)

    decision = policy_is_satisfied(policy, attributes)

    print("[attribute_authority] policy satisfied:", decision)

    if not decision:
        total_processing_ms = elapsed_ms(total_start)

        append_event({
            "component": "attribute_authority",
            "event_type": "access_request_denied",
            "request_id": request_id,
            "subscriber_id": subscriber_id,
            "topic": topic,
            "policy": policy,
            "attributes": attributes,
            "reason": "attributes_do_not_satisfy_policy",
        })

        append_metric({
            "component": "attribute_authority",
            "event_type": "access_request_denied",
            "message_id": f"request:{request_id}",
            "policy": policy,
            "success": False,
            "total_processing_ms": total_processing_ms,
            "error": "attributes_do_not_satisfy_policy",
        })

        print("[attribute_authority] access denied. No key generated.")
        return

    keygen_start = now_perf()
    keygen_stdout, keygen_stderr = abe.keygen(attributes)
    keygen_ms = elapsed_ms(keygen_start)

    key_hash = build_key_hash(
        request_id=request_id,
        subscriber_id=subscriber_id,
        topic=topic,
        policy=policy,
        attributes=attributes,
        keygen_stdout=keygen_stdout,
        keygen_stderr=keygen_stderr,
    )

    print("[attribute_authority] OpenABE keygen completed")
    print("keygen_ms:", keygen_ms)
    print("key_hash:", key_hash)

    chain_start = now_perf()
    receipt = blockchain.grant_key(request_id, key_hash)
    blockchain_grant_ms = elapsed_ms(chain_start)

    total_processing_ms = elapsed_ms(total_start)

    print("[attribute_authority] grantKey transaction")
    print("tx_hash:", receipt.get("tx_hash"))
    print("status:", receipt.get("status"))
    print("block_number:", receipt.get("block_number"))
    print("gas_used:", receipt.get("gas_used"))

    append_event({
        "component": "attribute_authority",
        "event_type": "key_grant_registered",
        "request_id": request_id,
        "subscriber_id": subscriber_id,
        "topic": topic,
        "policy": policy,
        "attributes": attributes,
        "key_hash": key_hash,
        "keygen_stdout": keygen_stdout,
        "keygen_stderr": keygen_stderr,
        "tx_hash": receipt.get("tx_hash", ""),
        "block_number": receipt.get("block_number", ""),
        "gas_used": receipt.get("gas_used", ""),
    })

    append_metric({
        "component": "attribute_authority",
        "event_type": "key_grant_registered",
        "message_id": f"request:{request_id}",
        "policy": policy,
        "success": True,
        "total_processing_ms": total_processing_ms,
        "tx_hash": receipt.get("tx_hash", ""),
        "block_number": receipt.get("block_number", ""),
        "gas_used": receipt.get("gas_used", ""),
        "error": "",
    })

    append_event({
        "component": "attribute_authority",
        "event_type": "attribute_authority_timing",
        "request_id": request_id,
        "subscriber_id": subscriber_id,
        "topic": topic,
        "keygen_ms": keygen_ms,
        "blockchain_grant_ms": blockchain_grant_ms,
        "total_processing_ms": total_processing_ms,
    })

    print("[attribute_authority] key grant completed successfully.")


def run_once(attributes: str):
    print("[attribute_authority] checking pending access requests")
    pending = blockchain.get_pending_access_requests()

    print("[attribute_authority] pending requests:", pending)

    if not pending:
        print("[attribute_authority] no pending requests found.")
        return

    for request in pending:
        process_request(request, attributes)


def run_loop(attributes: str, interval: float):
    print("[attribute_authority] starting service loop")
    print("attributes:", attributes)
    print("interval:", interval)

    while True:
        try:
            run_once(attributes)
        except Exception as exc:
            error_text = str(exc)

            print("[attribute_authority][ERROR]", error_text)

            append_event({
                "component": "attribute_authority",
                "event_type": "attribute_authority_error",
                "error": error_text,
            })

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description="Attribute Authority service for the integrated PoC."
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Process pending access requests once and exit."
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Polling interval in seconds for continuous mode."
    )

    parser.add_argument(
        "--attributes",
        default=DEFAULT_AUTHORIZED_ATTRIBUTES,
        help="Attributes assigned to the subscriber. Example: '|attr1'"
    )

    args = parser.parse_args()

    if args.once:
        run_once(args.attributes)
    else:
        run_loop(args.attributes, args.interval)


if __name__ == "__main__":
    main()
