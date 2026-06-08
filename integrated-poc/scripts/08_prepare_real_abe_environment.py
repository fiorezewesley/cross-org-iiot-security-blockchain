from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from openabe_client import OpenABEClient
from config import DEFAULT_AUTHORIZED_ATTRIBUTES


def main():
    abe = OpenABEClient()

    print("[PoC] Preparing real OpenABE environment")
    print("-" * 80)

    print("[1] Checking container")
    print(abe.check_container())
    print("-" * 80)

    print("[2] Running setup")
    stdout, stderr = abe.setup()
    print("stdout:", stdout)
    print("stderr:", stderr)
    print("-" * 80)

    print("[3] Generating authorized user key")
    print("attributes:", DEFAULT_AUTHORIZED_ATTRIBUTES)
    stdout, stderr = abe.keygen(DEFAULT_AUTHORIZED_ATTRIBUTES)
    print("stdout:", stdout)
    print("stderr:", stderr)
    print("-" * 80)

    print("[OK] Real OpenABE environment prepared.")


if __name__ == "__main__":
    main()
