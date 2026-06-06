#!/usr/bin/env bash

set -e

echo "============================================================"
echo "[PoC] Running on-chain validation flow"
echo "============================================================"

python3 integrated-poc/scripts/01_validate_blockchain_connection.py

echo
python3 integrated-poc/scripts/02_bootstrap_onchain_state.py

echo
python3 integrated-poc/scripts/03_request_access.py

echo
python3 integrated-poc/scripts/04_simulate_key_grant.py

echo
python3 integrated-poc/scripts/05_register_protected_message.py

echo
python3 integrated-poc/scripts/06_register_consumption_event.py --success

echo "============================================================"
echo "[OK] On-chain validation flow completed successfully."
echo "============================================================"
