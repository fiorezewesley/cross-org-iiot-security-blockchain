import os
import time
import json
import hashlib
from typing import Optional, Tuple

from web3 import Web3
import paho.mqtt.client as mqtt


# Environment variable settings
BESU_HTTP_URL = os.getenv("BESU_HTTP_URL", "http://besu-node:8545")

# I set to accept either MQTT_BROKER (preferred) or MQTT_HOST (fallback).
MQTT_HOST = os.getenv("MQTT_BROKER", os.getenv("MQTT_HOST", "mosquitto-broker"))
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

CONTRACT_ADDRESS = (os.getenv("CONTRACT_ADDRESS") or "").strip()
DEPLOYER_PRIVATE_KEY = (os.getenv("DEPLOYER_PRIVATE_KEY") or "").strip()

CHAIN_ID_ENV = os.getenv("CHAIN_ID")

MQTT_TEST_TOPIC = "test/hello"
MQTT_SENSOR_TOPIC = "sensors/#" 


# Minimum Contract ABI 
ENCRYPTED_DATA_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "deviceId", "type": "string"},
            {"internalType": "string", "name": "topic", "type": "string"},
            {"internalType": "string", "name": "abePolicy", "type": "string"},
            {"internalType": "string", "name": "cipherHash", "type": "string"},
        ],
        "name": "storeRecord",
        "outputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "name": "getRecord",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "lastId",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


# BEsu connection
def wait_for_besu(max_tries: int = 15, delay: int = 4) -> Optional[Web3]:
    print(f"[orchestrator] Testando conexão com Besu em {BESU_HTTP_URL}")

    for attempt in range(1, max_tries + 1):
        try:
            w3 = Web3(Web3.HTTPProvider(BESU_HTTP_URL))

            if w3.is_connected():
                print(f"[orchestrator] Conectado ao Besu! Versão: {w3.client_version}")
                return w3

            print(
                f"[orchestrator] Tentativa {attempt}/{max_tries}: "
                f"não conectou (is_connected() = False). Aguardando {delay}s..."
            )
        except Exception as e:
            print(
                f"[orchestrator] Tentativa {attempt}/{max_tries}: "
                f"erro ao conectar no Besu: {e}. Aguardando {delay}s..."
            )

        time.sleep(delay)

    print("[orchestrator] ERRO: Não conectou no Besu após várias tentativas.")
    return None


def test_besu_basic_calls(w3: Optional[Web3]) -> None:
    if w3 is None:
        print("[orchestrator] Besu não disponível, pulando testes de RPC.")
        return

    try:
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number

        try:
            coinbase = w3.eth.coinbase
        except Exception:
            coinbase = None

        print(f"[orchestrator] chain_id = {chain_id}")
        print(f"[orchestrator] último bloco = {block_number}")
        if coinbase:
            print(f"[orchestrator] coinbase = {coinbase}")
        else:
            print("[orchestrator] coinbase não disponível ou não configurado.")
    except Exception as e:
        print(f"[orchestrator] ERRO ao realizar chamadas básicas no Besu: {e}")


# Contract + sender
def make_contract(w3: Web3):
    if not CONTRACT_ADDRESS:
        raise RuntimeError("CONTRACT_ADDRESS não definido no ambiente.")
    checksum = Web3.to_checksum_address(CONTRACT_ADDRESS)
    return w3.eth.contract(address=checksum, abi=ENCRYPTED_DATA_REGISTRY_ABI)


def get_sender_account(w3: Web3):
    if not DEPLOYER_PRIVATE_KEY:
        raise RuntimeError("DEPLOYER_PRIVATE_KEY não definida (use chave DEV).")

    acct = w3.eth.account.from_key(DEPLOYER_PRIVATE_KEY)
    print(f"[orchestrator] sender address (from private key) = {acct.address}")
    return acct


def contract_sanity_check(contract) -> None:
    last_id = contract.functions.lastId().call()
    print(f"[orchestrator] Contrato OK. lastId() = {last_id}")


def send_store_record(
    w3: Web3,
    contract,
    device_id: str,
    topic: str,
    abe_policy: str,
    cipher_hash: str,
) -> Tuple[str, int]:
    """
    Envia storeRecord e espera receipt.
    Retorna (tx_hash_hex, status_receipt).
    """
    acct = get_sender_account(w3)
    sender = acct.address

    nonce = w3.eth.get_transaction_count(sender, "pending")

    # In devnet: use low gasPrice and a "high" gas_limit
    gas_limit = 1_200_000
    gas_price = w3.to_wei(1, "gwei")

    # chainId: prefer the node's; but if CHAIN_ID is set, I'll use it.
    chain_id = int(CHAIN_ID_ENV) if (CHAIN_ID_ENV and CHAIN_ID_ENV.isdigit()) else w3.eth.chain_id

    tx = contract.functions.storeRecord(
        device_id,
        topic,
        abe_policy,
        cipher_hash
    ).build_transaction(
        {
            "from": sender,
            "nonce": nonce,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": chain_id,
        }
    )

    signed = w3.eth.account.sign_transaction(tx, private_key=DEPLOYER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    tx_hex = tx_hash.hex()
    print(f"[orchestrator] storeRecord enviado. tx_hash={tx_hex} aguardando receipt...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(
        f"[orchestrator] receipt status={receipt.status} "
        f"block={receipt.blockNumber} gasUsed={receipt.gasUsed}"
    )

    return tx_hex, receipt.status


# MQTT: TEST + LISTENER
def test_mqtt_publish() -> None:
    print(f"[orchestrator] Testando conexão MQTT em {MQTT_HOST}:{MQTT_PORT}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print(f"[orchestrator] Conectado ao MQTT com código {reason_code}")

    client.on_connect = on_connect

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    payload = "Olá do orchestrator!"
    result = client.publish(MQTT_TEST_TOPIC, payload)
    status = result[0]

    if status == mqtt.MQTT_ERR_SUCCESS:
        print(f"[orchestrator] Mensagem publicada em '{MQTT_TEST_TOPIC}': {payload}")
    else:
        print(f"[orchestrator] ERRO ao publicar em '{MQTT_TEST_TOPIC}', status={status}")

    time.sleep(2)
    client.loop_stop()
    client.disconnect()


def start_mqtt_sensor_listener(w3: Web3, contract):
    print(
        f"[orchestrator] Iniciando listener MQTT de sensores em "
        f"{MQTT_HOST}:{MQTT_PORT}, tópico '{MQTT_SENSOR_TOPIC}'"
    )

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print(f"[orchestrator] Listener conectado ao MQTT, código={reason_code}")
        client.subscribe(MQTT_SENSOR_TOPIC)
        print(f"[orchestrator] Assinado tópico '{MQTT_SENSOR_TOPIC}'")

    def on_message(client, userdata, msg):
        payload_text = msg.payload.decode("utf-8", errors="ignore")
        print(f"[orchestrator] [MQTT SENSOR] tópico='{msg.topic}' payload_raw='{payload_text}'")

        
        try:
            data = json.loads(payload_text)
            print(f"[orchestrator] [MQTT SENSOR] payload_json={data}")
        except json.JSONDecodeError:
            data = {"raw": payload_text}

        device_id = data.get("sensor_id", "unknown")
        topic = msg.topic

        # placeholder (replace this with the real ABE later)
        abe_policy = "role:engineer AND org:A"
        cipher_hash = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()

        try:
            tx_hex, status = send_store_record(
                w3=w3,
                contract=contract,
                device_id=device_id,
                topic=topic,
                abe_policy=abe_policy,
                cipher_hash=cipher_hash,
            )
            print(f"[orchestrator] on-chain OK. status={status} tx={tx_hex}")
        except Exception as e:
            print(f"[orchestrator] ERRO ao registrar on-chain: {e}")

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client


# MAIN
def main():
    print("[orchestrator] Iniciando testes básicos...")

    # 1) Besu
    w3 = wait_for_besu()
    test_besu_basic_calls(w3)
    if w3 is None:
        print("[orchestrator] Encerrando: Besu indisponível.")
        return

    # 2) Contrato
    contract = make_contract(w3)
    contract_sanity_check(contract)

    # 3) MQTT sanity + listener
    test_mqtt_publish()
    sensor_client = start_mqtt_sensor_listener(w3, contract)

    print("[orchestrator] Testes concluídos. Mantendo container vivo...")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[orchestrator] Encerrando listener MQTT...")
        sensor_client.loop_stop()
        sensor_client.disconnect()


if __name__ == "__main__":
    main()
