#!/usr/bin/env bash
set -e

echo "[+] Subindo infraestrutura (Besu + Mosquitto + Orchestrator)..."
docker compose up -d --build

echo
echo "[+] Status dos containers:"
docker compose ps
