from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from ecies_utils import generate_ecies_keypair


def main():
    keys_dir = BASE_DIR / "runtime" / "keys" / "consumer_001"

    private_key_path = keys_dir / "subscriber_ecies_private.pem"
    public_key_path = keys_dir / "subscriber_ecies_public.pem"

    if private_key_path.exists() or public_key_path.exists():
        print("[WARN] ECIES keypair already exists.")
        print("private:", private_key_path)
        print("public:", public_key_path)
        return

    generate_ecies_keypair(private_key_path, public_key_path)

    print("[OK] Subscriber ECIES keypair generated.")
    print("private:", private_key_path)
    print("public:", public_key_path)


if __name__ == "__main__":
    main()
