# Multi-Organizational IIoT Data Sharing Using ABE and Blockchain

## Overview

This repository contains the implementation and documentation of a prototype architecture for secure data sharing between organizations in Industrial Internet of Things (IIoT) environments. The proposal combines MQTT-based communication, Attribute-Based Encryption (ABE), ECIES-based key protection, and blockchain-supported governance using Hyperledger Besu.

The implemented prototype validates an integrated workflow in which IIoT sensor data is protected off-chain using CP-ABE, transmitted through an MQTT broker, and governed through on-chain records related to devices, attributes, access policies, access requests, encrypted key grants, integrity hashes, and audit events. Sensitive sensor data and ABE cryptographic operations remain off-chain, while the blockchain layer provides traceability and coordination for access-related metadata.

## Research Objective

The main objective of this project is to investigate how MQTT, blockchain, and Attribute-Based Encryption (ABE) can support auditable, granular, and privacy-preserving data sharing in distributed IIoT scenarios involving multiple organizations.

## Current Scope

At its current stage, the repository includes:

* a local Hyperledger Besu network for on-chain governance records;
* an Eclipse Mosquitto broker for MQTT-based communication;
* an integrated proof-of-concept module for MQTT, ABE, ECIES, Attribute Authority, and blockchain interaction;
* a Solidity smart contract named `AccessPolicyRegistryV3`;
* Python orchestration scripts for environment bootstrap, sensor data collection, access requests, Attribute Authority processing, encrypted key retrieval, and payload decryption;
* an ABE module implemented and tested using the OpenABE library;
* ECIES-based utilities for protecting the delivery of OpenABE User Secret Keys (USKs);
* a Streamlit interface for guided execution and validation;
* technical documentation intended for academic evaluation and reproducibility.

## Architecture Summary

The architecture is organized into two main layers:

* **Off-chain operational layer:** includes IIoT devices, MQTT broker, producer-side and subscriber-side cryptographic frameworks, OpenABE-based CP-ABE operations, ECIES key protection, and the Attribute Authority.
* **On-chain governance layer:** implemented with Hyperledger Besu and the `AccessPolicyRegistryV3` smart contract, responsible for registering devices, attributes, topic policies, access requests, encrypted key grants, protected message metadata, integrity hashes, and audit events.

The integrated workflow can be summarized as:

```text
Sensor payload
→ Producer-side cryptographic framework
→ CP-ABE protected payload
→ MQTT broker
→ Subscriber-side cryptographic framework
→ USK retrieval and validation
→ CP-ABE decryption attempt
→ Plaintext recovery only when attributes satisfy the access policy
```

The blockchain does not store plaintext sensor data and does not execute ABE cryptographic operations. Its role is to coordinate and audit access-related records.

## Technology Stack

* Blockchain: Hyperledger Besu
* Smart Contracts: Solidity
* Smart Contract: `AccessPolicyRegistryV3`
* Messaging: Eclipse Mosquitto (MQTT)
* Backend and Orchestration: Python
* Blockchain Integration: Web3.py
* MQTT Integration: Paho-MQTT
* Cryptographic Method: CP-ABE with OpenABE
* Key Protection: ECIES
* Interface: Streamlit
* Infrastructure: Docker and Docker Compose

## Repository Structure

```text
.
├── abe-experiments/          # ABE experiments and cryptographic overhead evaluation
├── contracts/                # Solidity smart contracts used in earlier stages
├── docs/                     # Documentation for GitHub Pages
├── infra/                    # Infrastructure configuration files
├── integrated-poc/           # Integrated MQTT, ABE, ECIES, AA, and blockchain proof of concept
├── orchestrator/             # Python-based orchestration components
├── scripts/                  # Auxiliary scripts
├── docker-compose.yml        # Infrastructure definition
├── README.md                 # Repository overview
└── .gitignore                # Files ignored by Git
```

## Integrated Proof of Concept

The integrated proof of concept is available in:

```text
integrated-poc/
```

This module validates the complete workflow involving:

* on-chain bootstrap of producers, subscribers, attributes, and topic policies;
* MQTT-based sensor data collection;
* CP-ABE payload protection using OpenABE;
* access request registration on Hyperledger Besu;
* off-chain Attribute Authority processing;
* generation of OpenABE User Secret Keys associated with subscriber attributes;
* ECIES-based protection of the generated USK;
* encrypted key grant registration on-chain;
* subscriber-side encrypted key retrieval;
* integrity verification through hashes;
* decryption success when attributes satisfy the policy;
* decryption failure when attributes do not satisfy the policy.

## ABE Experiments for IIoT Sensor Payloads

The repository also includes experiments focused on the cryptographic behavior and overhead of ABE-based protection.

The ABE experiments are available in:

```text
abe-experiments/
```

This module evaluates:

* encryption and decryption correctness;
* processing overhead;
* ciphertext size expansion;
* Base64 encoding overhead;
* ABE-protected payload size;
* access policy complexity;
* accumulated overhead with real ESP32/DHT22 sensor measurements.

## Running the Environment

### Starting the base infrastructure

```bash
./scripts/01_start_infra.sh
```

### Running the integrated proof of concept

The integrated workflow is executed from the `integrated-poc/` directory. The module includes environment validation scripts, bootstrap scripts, Attribute Authority processing, encrypted key retrieval, and guided execution through the Streamlit interface.

For details, see:

```text
integrated-poc/README.md
```

## Documentation

The technical documentation is organized in the `docs/` directory and is published through GitHub Pages.

Documentation:

```text
https://fiorezewesley.github.io/cross-org-iiot-security-blockchain/
```

Source code repository:

```text
https://github.com/fiorezewesley/cross-org-iiot-security-blockchain
```

## Academic Context

This repository supports the dissertation entitled:

**Blockchain-Enabled ABE Framework for Secure IIoT Data Sharing Across Organizations**

The artifact was developed as part of a professional master's research project focused on secure cross-organizational IIoT data sharing, combining MQTT, Hyperledger Besu, smart contracts, and Attribute-Based Encryption.
