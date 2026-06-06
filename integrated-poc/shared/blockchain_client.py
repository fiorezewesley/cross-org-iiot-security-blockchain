import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from web3 import Web3

try:
    from .config import (
        BESU_RPC_URL,
        CONTRACT_ADDRESS,
        CONTRACT_ABI_PATH,
        PRIVATE_KEY,
        CHAIN_ID,
    )
except ImportError:
    from config import (
        BESU_RPC_URL,
        CONTRACT_ADDRESS,
        CONTRACT_ABI_PATH,
        PRIVATE_KEY,
        CHAIN_ID,
    )


class BlockchainClient:
    """
    Minimal Web3.py client for the integrated PoC.

    This class centralizes access to the AccessPolicyRegistry smart contract.
    It does not handle MQTT and does not perform ABE operations.
    """

    def __init__(
        self,
        rpc_url: str = BESU_RPC_URL,
        contract_address: str = CONTRACT_ADDRESS,
        abi_path: str = CONTRACT_ABI_PATH,
        private_key: str = PRIVATE_KEY,
        chain_id: int = CHAIN_ID,
    ) -> None:
        self.rpc_url = rpc_url
        self.contract_address = contract_address
        self.abi_path = Path(abi_path)
        self.private_key = private_key
        self.chain_id = chain_id

        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if not self.web3.is_connected():
            raise ConnectionError(f"Could not connect to Besu RPC at {self.rpc_url}")

        self.account = None
        if self.private_key:
            self.account = self.web3.eth.account.from_key(self.private_key)

        self.contract = None
        if self.contract_address and self.abi_path.exists():
            with open(self.abi_path, "r", encoding="utf-8") as f:
                abi = json.load(f)

            self.contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(self.contract_address),
                abi=abi,
            )

    def require_contract(self) -> None:
        if self.contract is None:
            raise RuntimeError(
                "Contract not configured. Set ACCESS_POLICY_CONTRACT_ADDRESS "
                "and ACCESS_POLICY_CONTRACT_ABI."
            )

    def require_account(self) -> None:
        if self.account is None:
            raise RuntimeError(
                "PRIVATE_KEY not configured. It is required to send transactions."
            )

    def get_chain_id(self) -> int:
        return self.web3.eth.chain_id

    def get_block_number(self) -> int:
        return self.web3.eth.block_number

    def get_sender_address(self) -> str:
        self.require_account()
        return self.account.address

    def _send_transaction(self, function_call: Any) -> Dict[str, Any]:
        self.require_account()

        nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")

        tx = function_call.build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "chainId": self.chain_id,
                "gas": 3_000_000,
                "gasPrice": self.web3.to_wei(1, "gwei"),
            }
        )

        signed_tx = self.web3.eth.account.sign_transaction(
            tx,
            private_key=self.private_key,
        )

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "tx_hash": tx_hash.hex(),
            "status": receipt.status,
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
        }

    # ---------- Write operations ----------

    def register_device(
        self,
        device_id: str,
        organization: str,
        role: str,
    ) -> Dict[str, Any]:
        self.require_contract()
        fn = self.contract.functions.registerDevice(
            device_id,
            organization,
            role,
        )
        return self._send_transaction(fn)

    def register_topic_policy(
        self,
        topic: str,
        policy: str,
    ) -> Dict[str, Any]:
        self.require_contract()
        fn = self.contract.functions.registerTopicPolicy(topic, policy)
        return self._send_transaction(fn)

    def request_access(
        self,
        subscriber_id: str,
        topic: str,
    ) -> Dict[str, Any]:
        self.require_contract()
        fn = self.contract.functions.requestAccess(subscriber_id, topic)
        return self._send_transaction(fn)

    def grant_key(
        self,
        request_id: int,
        usk_hash: str,
    ) -> Dict[str, Any]:
        self.require_contract()
        fn = self.contract.functions.grantKey(request_id, usk_hash)
        return self._send_transaction(fn)

    def store_protected_message(
        self,
        producer_id: str,
        topic: str,
        ciphertext_hash: str,
    ) -> Dict[str, Any]:
        self.require_contract()
        fn = self.contract.functions.storeProtectedMessage(
            producer_id,
            topic,
            ciphertext_hash,
        )
        return self._send_transaction(fn)

    def store_consumption_event(
        self,
        subscriber_id: str,
        topic: str,
        success: bool,
        result_hash: str,
    ) -> Dict[str, Any]:
        self.require_contract()
        fn = self.contract.functions.storeConsumptionEvent(
            subscriber_id,
            topic,
            success,
            result_hash,
        )
        return self._send_transaction(fn)

    # ---------- Read operations ----------

    def get_topic_policy(self, topic: str) -> str:
        self.require_contract()
        return self.contract.functions.getTopicPolicy(topic).call()

    def has_key_grant(self, request_id: int) -> bool:
        self.require_contract()
        return self.contract.functions.hasKeyGrant(request_id).call()

    def get_key_grant(self, request_id: int) -> Tuple[str, str, str, int]:
        self.require_contract()
        return self.contract.functions.getKeyGrant(request_id).call()

    def get_last_request_id(self) -> int:
        self.require_contract()
        return self.contract.functions.lastRequestId().call()

    def get_access_request(self, request_id: int) -> Dict[str, Any]:
        self.require_contract()

        result = self.contract.functions.accessRequests(request_id).call()

        return {
            "request_id": result[0],
            "subscriber_id": result[1],
            "topic": result[2],
            "timestamp": result[3],
            "granted": result[4],
            "exists": result[5],
        }

    def get_pending_access_requests(self) -> list[Dict[str, Any]]:
        self.require_contract()

        last_id = self.get_last_request_id()
        pending = []

        for request_id in range(1, last_id + 1):
            request = self.get_access_request(request_id)

            if request["exists"] and not request["granted"]:
                pending.append(request)

        return pending


if __name__ == "__main__":
    client = BlockchainClient(
        contract_address="",
        abi_path="",
        private_key="",
    )

    print("[blockchain_client] Connected to Besu")
    print(f"[blockchain_client] RPC: {client.rpc_url}")
    print(f"[blockchain_client] chain_id: {client.get_chain_id()}")
    print(f"[blockchain_client] block_number: {client.get_block_number()}")
