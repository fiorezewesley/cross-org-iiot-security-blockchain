from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from blockchain_client import BlockchainClient


def main():
    client = BlockchainClient()

    print("[PoC] Blockchain connection validation")
    print("-" * 80)
    print("Connected:", client.web3.is_connected())
    print("Chain ID:", client.get_chain_id())
    print("Current block:", client.get_block_number())
    print("Contract:", client.contract_address)
    print("Sender:", client.get_sender_address())
    print("lastRequestId:", client.get_last_request_id())
    print("-" * 80)
    print("[OK] Python/Web3.py can access Besu and AccessPolicyRegistry.")


if __name__ == "__main__":
    main()
