import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

# RPC do Besu.
# Quando rodar do host Ubuntu: http://127.0.0.1:8545
# Quando rodar de outro container na mesma rede Docker: http://besu-node:8545
BESU_RPC_URL = os.getenv("BESU_RPC_URL", "http://127.0.0.1:8545")

# Endereço do contrato AccessPolicyRegistry após deploy.
CONTRACT_ADDRESS = os.getenv("ACCESS_POLICY_CONTRACT_ADDRESS", "")

# Caminho padrão do ABI gerado após deploy.
CONTRACT_ABI_PATH = os.getenv(
    "ACCESS_POLICY_CONTRACT_ABI",
    str(BASE_DIR / "runtime" / "AccessPolicyRegistry_abi.json")
)

# Chave privada usada para assinar transações na rede Besu local.
# Deve ser carregada via variável de ambiente. Não versionar chaves.
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

# Conta derivada da PRIVATE_KEY. Será calculada pelo blockchain_client.py.
CHAIN_ID = int(os.getenv("CHAIN_ID", "1337"))

# Tópicos MQTT da PoC integrada.
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

TOPIC_PLAIN_PATTERN = os.getenv("TOPIC_PLAIN_PATTERN", "sensors/+/plain")
TOPIC_PROTECTED_PATTERN = os.getenv("TOPIC_PROTECTED_PATTERN", "sensors/+/protected")

DEFAULT_SENSOR_ID = os.getenv("DEFAULT_SENSOR_ID", "sensor_001")
DEFAULT_PRODUCER_ID = os.getenv("DEFAULT_PRODUCER_ID", "sensor_001")
DEFAULT_SUBSCRIBER_ID = os.getenv("DEFAULT_SUBSCRIBER_ID", "consumer_001")

DEFAULT_PLAIN_TOPIC = os.getenv(
    "DEFAULT_PLAIN_TOPIC",
    "sensors/sensor_001/plain"
)

DEFAULT_PROTECTED_TOPIC = os.getenv(
    "DEFAULT_PROTECTED_TOPIC",
    "sensors/sensor_001/protected"
)

DEFAULT_DECRYPTED_TOPIC = os.getenv(
    "DEFAULT_DECRYPTED_TOPIC",
    "sensors/sensor_001/decrypted"
)

# Política inicial simples, compatível com os testes OpenABE já validados.
DEFAULT_ABE_POLICY = os.getenv("DEFAULT_ABE_POLICY", "attr1 or attr2")
DEFAULT_AUTHORIZED_ATTRIBUTES = os.getenv("DEFAULT_AUTHORIZED_ATTRIBUTES", "|attr1")
DEFAULT_UNAUTHORIZED_ATTRIBUTES = os.getenv("DEFAULT_UNAUTHORIZED_ATTRIBUTES", "|attr3")

# Container OpenABE já existente.
OPENABE_CONTAINER = os.getenv("OPENABE_CONTAINER", "openabe-lab-split-test")
OPENABE_WORKDIR = os.getenv("OPENABE_WORKDIR", "/openabe/examples")
OPENABE_BINARY = os.getenv("OPENABE_BINARY", "/openabe/examples/cpabe_split")

# Runtime local da PoC. Não deve ser versionado.
RUNTIME_DIR = BASE_DIR / "runtime"
KEYS_DIR = RUNTIME_DIR / "keys"
