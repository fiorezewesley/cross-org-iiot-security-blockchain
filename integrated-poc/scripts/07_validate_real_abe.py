from pathlib import Path
import sys
import json
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from openabe_client import OpenABEClient
from config import DEFAULT_ABE_POLICY, DEFAULT_AUTHORIZED_ATTRIBUTES


def main():
    abe = OpenABEClient()

    print("[PoC] Real OpenABE validation")
    print("-" * 80)

    print("[1] Checking OpenABE container and binary")
    print(abe.check_container())
    print("-" * 80)

    print("[2] Running CP-ABE setup")
    stdout, stderr = abe.setup()
    print("stdout:", stdout)
    print("stderr:", stderr)
    print("-" * 80)

    print("[3] Generating user secret key")
    print("attributes:", DEFAULT_AUTHORIZED_ATTRIBUTES)
    stdout, stderr = abe.keygen(DEFAULT_AUTHORIZED_ATTRIBUTES)
    print("stdout:", stdout)
    print("stderr:", stderr)
    print("-" * 80)

    plaintext_payload = {
        "sensor_id": "sensor_001",
        "temperature": 23.7,
        "humidity": 60,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    plaintext = json.dumps(plaintext_payload, separators=(",", ":"), sort_keys=True)

    print("[4] Plaintext")
    print(plaintext)
    print("-" * 80)

    print("[5] Encrypting with real OpenABE")
    print("policy:", DEFAULT_ABE_POLICY)
    encrypted = abe.encrypt_to_b64(plaintext, DEFAULT_ABE_POLICY)
    print("ciphertext_bin_bytes:", encrypted["ciphertext_bin_bytes"])
    print("ciphertext_b64_bytes:", encrypted["ciphertext_b64_bytes"])
    print("ciphertext_b64_preview:", encrypted["ciphertext_b64"][:120] + "...")
    print("-" * 80)

    print("[6] Decrypting with real OpenABE")
    recovered = abe.decrypt_from_b64(encrypted["ciphertext_b64"])
    print("recovered:")
    print(recovered)
    print("-" * 80)

    if plaintext not in recovered and recovered.strip() != plaintext:
        raise RuntimeError(
            "Decryption ran, but recovered plaintext does not match the original payload."
        )

    print("[OK] Real OpenABE encryption/decryption validated.")


if __name__ == "__main__":
    main()
