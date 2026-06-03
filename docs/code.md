# Source Code and Repository Structure

## Overview

This page provides a guided view of the source code currently available in the repository.

The repository contains two complementary experimental layers:

1. an MQTT-blockchain integration prototype;
2. an isolated Attribute-Based Encryption (ABE) experimental module for IIoT sensor payload protection.

The ABE module is evaluated independently from the blockchain layer. Therefore, the current source code should not be interpreted as a complete end-to-end MQTT-ABE-blockchain implementation.

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

### 4. ABE Experiments

**Path:** `abe-experiments/`

This directory contains the experimental Attribute-Based Encryption module used to evaluate cryptographic protection over IIoT sensor payloads.

Main subdirectories:

- `abe-experiments/scripts/`
- `abe-experiments/results/`
- `abe-experiments/docs/`

The scripts include:

- producer-side ABE encryption module
- subscriber-side ABE decryption module
- payload size overhead experiment
- access policy complexity overhead experiment
- real sensor message volume experiment

The results directory contains CSV files generated from the experiments. These files provide quantitative evidence about encryption time, decryption time, ciphertext expansion, MQTT protected message overhead, policy complexity, and real sensor message volume.

The documentation directory includes a practical procedure for executing tests with real sensor data.

## Access to the Code

The source code can be accessed directly through the GitHub repository:

- [Repository main page](https://github.com/fiorezewesley/cross-org-iiot-security-blockchain)

The ABE experimental module is available at:

- [ABE experiments directory](https://github.com/fiorezewesley/cross-org-iiot-security-blockchain/tree/main/abe-experiments)
