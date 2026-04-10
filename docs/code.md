# Source Code and Repository Structure

## Overview

This page provides a guided view of the source code currently available in the repository.

## Main Repository Components

### 1. Smart Contracts

**Path:** `contracts/`

This directory contains the Solidity smart contracts used in the blockchain layer.

Main artifact:

- `EncryptedDataRegistry.sol`

Its role is to register metadata associated with IIoT messages, preserving an auditable and immutable on-chain record while keeping sensitive content off-chain.

### 2. Orchestrator

**Path:** `orchestrator/`

This directory contains the Python-based orchestration service responsible for integrating MQTT communication with blockchain transactions.

Relevant responsibilities:

- connecting to the MQTT broker
- receiving sensor messages
- generating metadata and hashes
- submitting transactions to the smart contract

### 3. Infrastructure

**Path:** project root + `scripts/` + infrastructure folders

The infrastructure layer includes:

- `docker-compose.yml`
- startup scripts
- Mosquitto configuration files
- service definitions for reproducible execution

Its purpose is to provide an isolated and repeatable experimental environment.

## Access to the Code

The source code can be accessed directly through the GitHub repository:

- [Repository main page](https://github.com/fiorezewesley/cross-org-iiot-security-blockchain)

