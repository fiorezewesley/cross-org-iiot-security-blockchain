from pathlib import Path
import sys
import argparse
import json
import base64

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient
from ecies_utils import ecies_decrypt
from hash_utils import sha256_text
from poc_logger import append_event, append_metric, elapsed_ms, now_perf


PRIVATE_KEY_PATH = (
    BASE_DIR / "runtime" / "keys" / "consumer_001" / "subscriber_ecies_private.pem"
)


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve encUSK from blockchain and decrypt it using the subscriber ECIES private key."
    )

    parser.add_argument(
        "--request-id",
        type=int,
        required=True,
        help="Access request identifier."
    )

    args = parser.parse_args()

    total_start = now_perf()

    client = BlockchainClient()

    print("[subscriber_key_retrieval] retrieving encrypted key grant")
    print("request_id:", args.request_id)
    print("-" * 80)

    grant = client.get_encrypted_key_grant(args.request_id)

    encrypted_user_key = grant["encrypted_user_key"]
    stored_hash = grant["key_hash"]

    print("[subscriber_key_retrieval] grant metadata")
    print("subscriber_id:", grant["subscriber_id"])
    print("topic:", grant["topic"])
    print("key_hash:", stored_hash)
    print("encrypted_user_key_bytes:", len(encrypted_user_key.encode("utf-8")))
    print("-" * 80)

    decrypt_start = now_perf()
    decrypted_usk = ecies_decrypt(
        encrypted_user_key,
        PRIVATE_KEY_PATH
    )
    ecies_decrypt_ms = elapsed_ms(decrypt_start)

    computed_hash = sha256_text(decrypted_usk)
    integrity_valid = computed_hash == stored_hash

    print("[subscriber_key_retrieval] decrypted USK artifact")
    print(decrypted_usk)
    print("-" * 80)

    print("[subscriber_key_retrieval] integrity verification")
    print("stored_hash:", stored_hash)
    print("computed_hash:", computed_hash)
    print("valid:", integrity_valid)
    print("ecies_decrypt_ms:", ecies_decrypt_ms)
    print("-" * 80)

    if not integrity_valid:
        raise RuntimeError("USK hash verification failed.")

    output_dir = BASE_DIR / "runtime" / "keys" / grant["subscriber_id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"retrieved_usk_request_{args.request_id}.json"
    output_path.write_text(decrypted_usk, encoding="utf-8")
    usk_artifact = json.loads(decrypted_usk)

    if usk_artifact.get("type") == "OpenABE_USER_SECRET_KEY_BINARY":
        restored_usk_bytes = base64.b64decode(usk_artifact["usk_b64"])

        restored_usk_path = output_dir / usk_artifact.get(
            "filename",
            f"usk_request_{args.request_id}.bin"
        )

        restored_usk_path.write_bytes(restored_usk_bytes)

        print("[subscriber_key_retrieval] real OpenABE USK restored")
        print("restored_usk_path:", restored_usk_path)
        print("restored_usk_size_bytes:", len(restored_usk_bytes))


    total_processing_ms = elapsed_ms(total_start)

    append_event({
        "component": "subscriber_key_retrieval",
        "event_type": "encrypted_usk_retrieved",
        "request_id": args.request_id,
        "subscriber_id": grant["subscriber_id"],
        "topic": grant["topic"],
        "key_hash": stored_hash,
        "computed_hash": computed_hash,
        "integrity_valid": integrity_valid,
        "encrypted_user_key_bytes": len(encrypted_user_key.encode("utf-8")),
        "ecies_decrypt_ms": ecies_decrypt_ms,
        "output_path": str(output_path),
    })

    append_metric({
        "component": "subscriber_key_retrieval",
        "event_type": "encrypted_usk_retrieved",
        "message_id": f"request:{args.request_id}",
        "success": True,
        "total_processing_ms": total_processing_ms,
        "result_hash": computed_hash,
        "error": "",
    })

    print("[OK] encUSK retrieved, decrypted and verified.")
    print("saved_to:", output_path)


if __name__ == "__main__":
    main()
