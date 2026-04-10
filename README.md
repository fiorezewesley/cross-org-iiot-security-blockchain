# Multi-Organizational IIoT Data Sharing Using ABE and Blockchain

## Overview

This repository contains the implementation and documentation of an architecture for data sharing between organizations in Industrial Internet of Things (IIoT) environments. The proposal combines blockchain, MQTT-based communication, and Attribute-Based Cryptography (ABE) to support privacy-preserving interoperability between distinct entities.

The current prototype focuses on the integration between a local blockchain network, an MQTT broker, and a Python-based orchestrator responsible for receiving IIoT messages and recording metadata on the blockchain. Sensitive content remains off the blockchain, while the blockchain maintains an immutable audit log of interactions.

## Research Objective

The main objective of this project is to investigate how MQTT, blockchain, and attribute-based cryptography (ABE) technologies can support auditable and granular data sharing in distributed IIoT scenarios involving multiple organizations, creating a viable interoperability architecture between these companies.

## Current Scope

At its current stage, the repository includes:

- a local Hyperledger Besu network for on-chain logging
- an Eclipse Mosquitto broker for MQTT-based communication
- a Python orchestrator for MQTT and blockchain integration
- a Solidity smart contract for metadata logging
- technical documentation intended for academic evaluation and reproducibility
- an ABE module implemented and tested using the OpenABE library

## Architecture Summary

The architecture is divided into three main layers:

- **Communication layer:** MQTT broker (Eclipse Mosquitto)
- **Coordination layer:** Python orchestrator
- **Audit and integrity layer:** ABE and Hyperledger Besu with Solidity smart contracts

The current experimental flow is:

IIoT device → MQTT broker → Orchestrator → Smart Contract on Besu

## Technology Stack

- Blockchain: Hyperledger Besu
- Smart Contracts: Solidity
- Messaging: Eclipse Mosquitto (MQTT)
- Backend: Python
- Blockchain Integration: Web3.py
- Cryptographic Method: ABE
- MQTT Integration: Paho MQTT
- Infrastructure: Docker and Docker Compose

## Repository Structure

```text

.

├── contracts/ # Solidity Smart Contracts
├── orchestrator/ # Python-based orchestration service
├── docs/ # Documentation for GitHub Pages
├── scripts/ # Auxiliary scripts
├── docker-compose.yml # Infrastructure definition
├── README.md # Repository overview
└── .gitignore # Files ignored by Git

```

## Running the Environment

### Starting the infrastructure

```bash
./scripts/01_start_infra.sh
```

### Testing the MQTT publication

```bash
mosquitto_pub -h localhost -p 1883 \

-t "sensors/sensor_001/data" -m '{"sensor_id": "sensor_001", "temp": 23.7, "humidity": 60}'

```

### Check blockchain chain ID

```bash
curl -s -X POST http://127.0.0.1:8545 \
-H "Content-Type: application/json" \
--data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'

```

Expected result:

```
0x539
```

## Documentation

The repository documentation is organized in the `docs/` directory and is intended for publication on GitHub Pages for dissertation evaluation and technical navigation.

## Future Work

Future versions of this repository will include the isolated ABE module and its integration into the main architecture as an experimental cryptographic component.