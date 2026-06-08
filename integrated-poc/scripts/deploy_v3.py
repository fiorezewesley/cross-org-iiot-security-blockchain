from pathlib import Path
import json
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

from web3 import Web3
from config import BESU_RPC_URL, PRIVATE_KEY, CHAIN_ID


ABI_PATH = BASE_DIR / "runtime" / "AccessPolicyRegistryV3_abi.json"
BYTECODE_PATH = BASE_DIR / "runtime" / "AccessPolicyRegistryV3_bytecode.txt"


def main():
    web3 = Web3(Web3.HTTPProvider(BESU_RPC_URL))

    if not web3.is_connected():
        raise RuntimeError(f"Could not connect to Besu RPC: {BESU_RPC_URL}")

    account = web3.eth.account.from_key(PRIVATE_KEY)

    abi = json.loads(ABI_PATH.read_text(encoding="utf-8"))
    bytecode = BYTECODE_PATH.read_text(encoding="utf-8").strip()

    if not bytecode.startswith("0x"):
        bytecode = "0x" + bytecode

    contract = web3.eth.contract(
        abi=abi,
        bytecode=bytecode,
    )

    nonce = web3.eth.get_transaction_count(account.address, "pending")

    print("[deploy_v3] Connected:", web3.is_connected())
    print("[deploy_v3] Chain ID:", web3.eth.chain_id)
    print("[deploy_v3] Deployer:", account.address)
    print("[deploy_v3] Nonce pending:", nonce)

    tx = contract.constructor().build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "gas": 7_000_000,
        "gasPrice": web3.to_wei(3, "gwei"),
    })

    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)

    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print("[deploy_v3] tx_hash:", tx_hash.hex())
    print("[deploy_v3] waiting receipt...")

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    print("-" * 80)
    print("[OK] AccessPolicyRegistryV3 deployed")
    print("status:", receipt.status)
    print("contract_address:", receipt.contractAddress)
    print("block_number:", receipt.blockNumber)
    print("gas_used:", receipt.gasUsed)
    print("tx_hash:", receipt.transactionHash.hex())


if __name__ == "__main__":
    main()

