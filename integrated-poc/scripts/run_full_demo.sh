#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
POC_DIR="$PROJECT_DIR/integrated-poc"

TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
RUN_DIR="$POC_DIR/runtime/demo_runs/$TIMESTAMP"

OPENABE_CONTAINER="openabe-lab-split-test"

mkdir -p "$RUN_DIR"

echo "================================================================================"
echo "IIoT ABE Blockchain PoC - Full Reproducible Demo"
echo "================================================================================"
echo "[INFO] Project directory: $PROJECT_DIR"
echo "[INFO] PoC directory: $POC_DIR"
echo "[INFO] Evidence directory: $RUN_DIR"
echo "================================================================================"

cd "$PROJECT_DIR"

run_step() {
    local step_name="$1"
    local log_file="$2"
    shift 2

    echo
    echo "================================================================================"
    echo "[STEP] $step_name"
    echo "================================================================================"

    {
        echo "================================================================================"
        echo "[STEP] $step_name"
        echo "[COMMAND] $*"
        echo "[START] $(date --iso-8601=seconds)"
        echo "================================================================================"
        "$@"
        echo "================================================================================"
        echo "[END] $(date --iso-8601=seconds)"
        echo "================================================================================"
    } 2>&1 | tee "$log_file"
}

run_inline_python() {
    local step_name="$1"
    local log_file="$2"
    local code="$3"

    echo
    echo "================================================================================"
    echo "[STEP] $step_name"
    echo "================================================================================"

    {
        echo "================================================================================"
        echo "[STEP] $step_name"
        echo "[START] $(date --iso-8601=seconds)"
        echo "================================================================================"
        PYTHONPATH=integrated-poc/shared python3 - <<PY
$code
PY
        echo "================================================================================"
        echo "[END] $(date --iso-8601=seconds)"
        echo "================================================================================"
    } 2>&1 | tee "$log_file"
}

run_step \
    "01 - Check environment" \
    "$RUN_DIR/01_check_environment.log" \
    python3 integrated-poc/scripts/check_environment.py

run_step \
    "02 - Bootstrap on-chain state" \
    "$RUN_DIR/02_bootstrap_onchain_state.log" \
    python3 integrated-poc/scripts/02_bootstrap_onchain_state.py

run_step \
    "03 - Register access request" \
    "$RUN_DIR/03_request_access.log" \
    python3 integrated-poc/scripts/03_request_access.py

REQUEST_ID="$(
    grep -E "lastRequestId:" "$RUN_DIR/03_request_access.log" \
    | tail -n 1 \
    | awk '{print $2}'
)"

if [[ -z "$REQUEST_ID" ]]; then
    echo "[ERROR] Could not extract request_id from 03_request_access.log"
    exit 1
fi

echo "[INFO] Extracted request_id: $REQUEST_ID" | tee "$RUN_DIR/request_id.txt"

run_step \
    "04 - Attribute Authority generates and grants encrypted USK" \
    "$RUN_DIR/04_attribute_authority.log" \
    python3 integrated-poc/attribute_authority/attribute_authority_service.py --once

run_step \
    "05 - Subscriber retrieves and decrypts encUSK" \
    "$RUN_DIR/05_retrieve_encrypted_usk.log" \
    python3 integrated-poc/subscriber_crypto/retrieve_encrypted_usk.py --request-id "$REQUEST_ID"

RESTORED_USK_PATH="integrated-poc/runtime/keys/consumer_001/usk_request_${REQUEST_ID}.bin"

if [[ ! -f "$RESTORED_USK_PATH" ]]; then
    echo "[ERROR] Restored USK file not found: $RESTORED_USK_PATH"
    exit 1
fi

echo
echo "================================================================================"
echo "[STEP] 06 - Copy restored USK into OpenABE container"
echo "================================================================================"

{
    echo "================================================================================"
    echo "[STEP] 06 - Copy restored USK into OpenABE container"
    echo "[START] $(date --iso-8601=seconds)"
    echo "================================================================================"

    docker cp \
        "$RESTORED_USK_PATH" \
        "$OPENABE_CONTAINER:/openabe/examples/state/usk_key0.bin"

    docker exec "$OPENABE_CONTAINER" ls -lh /openabe/examples/state/usk_key0.bin

    echo "================================================================================"
    echo "[END] $(date --iso-8601=seconds)"
    echo "================================================================================"
} 2>&1 | tee "$RUN_DIR/06_copy_usk_to_openabe_container.log"

run_inline_python \
    "07 - Decrypt current ABE ciphertext" \
    "$RUN_DIR/07_decrypt_payload.log" \
'
from openabe_client import OpenABEClient

abe = OpenABEClient()
stdout, stderr = abe.decrypt_current_ciphertext()

print("STDOUT:")
print(stdout)

print("STDERR:")
print(stderr)
'

run_inline_python \
    "08 - Generate demo summary" \
    "$RUN_DIR/08_generate_demo_summary.log" \
"
from pathlib import Path
import json
import re
from blockchain_client import BlockchainClient
from config import DEFAULT_SUBSCRIBER_ID, DEFAULT_PROTECTED_TOPIC

run_dir = Path('$RUN_DIR')
request_id = int('$REQUEST_ID')

client = BlockchainClient()

retrieve_log = (run_dir / '05_retrieve_encrypted_usk.log').read_text(encoding='utf-8', errors='ignore')
decrypt_log = (run_dir / '07_decrypt_payload.log').read_text(encoding='utf-8', errors='ignore')
aa_log = (run_dir / '04_attribute_authority.log').read_text(encoding='utf-8', errors='ignore')

policy = client.get_topic_policy(DEFAULT_PROTECTED_TOPIC)
attributes = client.get_subscriber_attributes(DEFAULT_SUBSCRIBER_ID)

valid_hash = 'valid: True' in retrieve_log
decrypt_success = '[decrypt] recovered message:' in decrypt_log

payload = None
match = re.search(r'\\[decrypt\\] recovered message: (\\{.*\\})', decrypt_log)
if match:
    try:
        payload = json.loads(match.group(1))
    except Exception:
        payload = match.group(1)

key_hash = None
match = re.search(r'key_hash:\\s*([a-fA-F0-9]+)', aa_log)
if match:
    key_hash = match.group(1)

grant_tx_hash = None
matches = re.findall(r'tx_hash:\\s*([a-fA-F0-9]+)', aa_log)
if matches:
    grant_tx_hash = matches[-1]

summary = {
    'demo_run_dir': str(run_dir),
    'contract_address': client.contract_address,
    'chain_id': client.web3.eth.chain_id,
    'request_id': request_id,
    'subscriber_id': DEFAULT_SUBSCRIBER_ID,
    'topic': DEFAULT_PROTECTED_TOPIC,
    'policy': policy,
    'subscriber_attributes': attributes,
    'attribute_source': 'blockchain',
    'aa_policy_decision': 'not_performed',
    'abe_enforcement_point': 'decryption',
    'key_hash': key_hash,
    'grant_tx_hash': grant_tx_hash,
    'key_hash_valid': valid_hash,
    'decryption_success': decrypt_success,
    'recovered_payload': payload,
}

(run_dir / 'demo_summary.json').write_text(
    json.dumps(summary, indent=2, ensure_ascii=False),
    encoding='utf-8'
)

print(json.dumps(summary, indent=2, ensure_ascii=False))

if not valid_hash:
    raise SystemExit('Hash validation failed.')

if not decrypt_success:
    raise SystemExit('ABE decryption failed.')
"

echo
echo "================================================================================"
echo "[OK] Full demo completed successfully."
echo "================================================================================"
echo "[INFO] Evidence saved to:"
echo "$RUN_DIR"
echo
echo "[INFO] Summary:"
cat "$RUN_DIR/demo_summary.json"
echo
