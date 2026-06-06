from pathlib import Path
import sys
import time
import argparse
import json
import base64
from datetime import datetime, timezone
from typing import Optional

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from openabe_client import OpenABEClient
from hash_utils import sha256_text
from poc_logger import append_event, append_metric, elapsed_ms, now_perf
from ecies_utils import ecies_encrypt


blockchain = BlockchainClient()
abe = OpenABEClient()

SUBSCRIBER_PUBLIC_KEY_PATH = (
    BASE_DIR / "runtime" / "keys" / "consumer_001" / "subscriber_ecies_public.pem"
)


def process_request(request: dict, attributes: Optional[str] = None):
    """
    Processes a blockchain access request.

    Correct CP-ABE behavior:
    - The Attribute Authority does not decide whether the subscriber satisfies
      the topic policy.
    - The Attribute Authority retrieves the subscriber attributes from the
      blockchain and generates an OpenABE user secret key for those attributes.
    - The effective access decision occurs later, during ABE decryption:
      if the attributes embedded in the user's key satisfy the ciphertext
      policy, decryption succeeds; otherwise, it fails.

    The optional 'attributes' argument is kept only for compatibility with
    older callers. It is ignored as an authoritative source.
    """

    total_start = now_perf()

    request_id = request["request_id"]
    subscriber_id = request["subscriber_id"]
    topic = request["topic"]

    print("-" * 80)
    print("[attribute_authority] processing access request")
    print("request_id:", request_id)
    print("subscriber_id:", subscriber_id)
    print("topic:", topic)

    # The policy is read only for logging and traceability.
    # The AA does not use it to decide whether to generate the key.
    policy = blockchain.get_topic_policy(topic)

    # The subscriber attributes are retrieved from the blockchain.
    # These attributes are used to generate the OpenABE user secret key.
    attributes_from_chain = blockchain.get_subscriber_attributes(subscriber_id)

    print("[attribute_authority] topic policy from blockchain:", policy)
    print("[attribute_authority] subscriber attributes from blockchain:", attributes_from_chain)
    print("[attribute_authority] generating OpenABE USK for subscriber attributes")

    if attributes and attributes != attributes_from_chain:
        print(
            "[attribute_authority][WARN] CLI/manual attributes ignored. "
            "Blockchain attributes are being used as authoritative source."
        )
        print("[attribute_authority][WARN] manual attributes:", attributes)

    attributes = attributes_from_chain

    append_event({
        "component": "attribute_authority",
        "event_type": "access_request_detected",
        "request_id": request_id,
        "subscriber_id": subscriber_id,
        "topic": topic,
        "policy": policy,
        "attributes": attributes,
        "attribute_source": "blockchain",
        "aa_behavior": (
            "AA generates an OpenABE user secret key from blockchain-registered "
            "subscriber attributes. Policy satisfaction is enforced by CP-ABE "
            "during decryption, not by a manual AA decision."
        ),
    })

    if not attributes:
        total_processing_ms = elapsed_ms(total_start)

        append_event({
            "component": "attribute_authority",
            "event_type": "access_request_failed",
            "request_id": request_id,
            "subscriber_id": subscriber_id,
            "topic": topic,
            "policy": policy,
            "attributes": attributes,
            "attribute_source": "blockchain",
            "reason": "subscriber_has_no_registered_attributes",
        })

        append_metric({
            "component": "attribute_authority",
            "event_type": "access_request_failed",
            "message_id": f"request:{request_id}",
            "policy": policy,
            "success": False,
            "total_processing_ms": total_processing_ms,
            "error": "subscriber_has_no_registered_attributes",
        })

        print("[attribute_authority][ERROR] subscriber has no registered attributes.")
        return

    if not SUBSCRIBER_PUBLIC_KEY_PATH.exists():
        raise FileNotFoundError(
            f"Subscriber public key not found: {SUBSCRIBER_PUBLIC_KEY_PATH}. "
            "Run 09_generate_subscriber_ecies_keypair.py first."
        )

    keygen_start = now_perf()
    keygen_stdout, keygen_stderr = abe.keygen(attributes)
    keygen_ms = elapsed_ms(keygen_start)

    exported_usk_path = (
        BASE_DIR
        / "runtime"
        / "openabe_exports"
        / subscriber_id
        / f"usk_request_{request_id}.bin"
    )

    abe.export_usk_from_container(exported_usk_path)

    usk_bytes = exported_usk_path.read_bytes()
    usk_b64 = base64.b64encode(usk_bytes).decode("utf-8")

    usk_artifact = {
        "type": "OpenABE_USER_SECRET_KEY_BINARY",
        "request_id": request_id,
        "subscriber_id": subscriber_id,
        "topic": topic,
        "policy": policy,
        "attributes": attributes,
        "attribute_source": "blockchain",
        "filename": exported_usk_path.name,
        "usk_size_bytes": len(usk_bytes),
        "usk_b64": usk_b64,
        "keygen_stdout": keygen_stdout,
        "keygen_stderr": keygen_stderr,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "This artifact contains the real OpenABE user secret key generated "
            "from the subscriber attributes registered on the blockchain. "
            "The AA does not manually evaluate the topic policy. The effective "
            "policy enforcement occurs during CP-ABE decryption."
        ),
    }

    usk_artifact_json = json.dumps(
        usk_artifact,
        separators=(",", ":"),
        sort_keys=True,
    )

    key_hash = sha256_text(usk_artifact_json)

    ecies_start = now_perf()
    encrypted_user_key = ecies_encrypt(
        usk_artifact_json,
        SUBSCRIBER_PUBLIC_KEY_PATH,
    )
    ecies_encrypt_ms = elapsed_ms(ecies_start)

    print("[attribute_authority] OpenABE keygen completed")
    print("keygen_ms:", keygen_ms)
    print("[attribute_authority] ECIES protection completed")
    print("ecies_encrypt_ms:", ecies_encrypt_ms)
    print("key_hash:", key_hash)
    print("exported_usk_path:", exported_usk_path)
    print("usk_size_bytes:", len(usk_bytes))
    print("encUSK bytes:", len(encrypted_user_key.encode("utf-8")))

    chain_start = now_perf()
    receipt = blockchain.grant_encrypted_key(
        request_id,
        encrypted_user_key,
        key_hash,
    )
    blockchain_grant_ms = elapsed_ms(chain_start)

    total_processing_ms = elapsed_ms(total_start)

    print("[attribute_authority] grantEncryptedKey transaction")
    print("tx_hash:", receipt.get("tx_hash"))
    print("status:", receipt.get("status"))
    print("block_number:", receipt.get("block_number"))
    print("gas_used:", receipt.get("gas_used"))

    append_event({
        "component": "attribute_authority",
        "event_type": "encrypted_key_grant_registered",
        "request_id": request_id,
        "subscriber_id": subscriber_id,
        "topic": topic,
        "policy": policy,
        "attributes": attributes,
        "attribute_source": "blockchain",
        "aa_policy_decision": "not_performed",
        "abe_enforcement_point": "decryption",
        "key_hash": key_hash,
        "encrypted_user_key_bytes": len(encrypted_user_key.encode("utf-8")),
        "tx_hash": receipt.get("tx_hash", ""),
        "block_number": receipt.get("block_number", ""),
        "gas_used": receipt.get("gas_used", ""),
        "keygen_ms": keygen_ms,
        "ecies_encrypt_ms": ecies_encrypt_ms,
        "blockchain_grant_ms": blockchain_grant_ms,
        "total_processing_ms": total_processing_ms,
    })

    append_metric({
        "component": "attribute_authority",
        "event_type": "encrypted_key_grant_registered",
        "message_id": f"request:{request_id}",
        "policy": policy,
        "success": True,
        "total_processing_ms": total_processing_ms,
        "tx_hash": receipt.get("tx_hash", ""),
        "block_number": receipt.get("block_number", ""),
        "gas_used": receipt.get("gas_used", ""),
        "error": "",
    })

    print("[attribute_authority] encrypted key grant completed successfully.")
    print("[attribute_authority] CP-ABE policy enforcement will occur during decryption.")


def run_once():
    print("[attribute_authority] checking pending access requests")
    pending = blockchain.get_pending_access_requests()

    print("[attribute_authority] pending requests:", pending)

    if not pending:
        print("[attribute_authority] no pending requests found.")
        return

    for request in pending:
        process_request(request)


def run_loop(interval: float):
    print("[attribute_authority] starting service loop")
    print("attribute_source: blockchain")
    print("aa_policy_decision: not_performed")
    print("abe_enforcement_point: decryption")
    print("interval:", interval)

    while True:
        try:
            run_once()
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
        description=(
            "Attribute Authority service that generates OpenABE user secret "
            "keys from blockchain-registered subscriber attributes and protects "
            "them with ECIES. The AA does not manually evaluate CP-ABE access "
            "policies; policy enforcement occurs during ABE decryption."
        )
    )

    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=5.0)

    parser.add_argument(
        "--attributes",
        default=None,
        help=(
            "Legacy argument kept for compatibility. "
            "Ignored as authoritative source. Subscriber attributes are retrieved "
            "from the blockchain."
        ),
    )

    args = parser.parse_args()

    if args.once:
        run_once()
    else:
        run_loop(args.interval)


if __name__ == "__main__":
    main()