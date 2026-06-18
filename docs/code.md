# Source Code and Repository Structure

## Overview

This page provides a guided view of the source code currently available in the repository.

The repository contains an integrated proof of concept for secure cross-organizational IIoT data sharing, combining MQTT-based communication, CP-ABE payload protection, ECIES-based key protection, an off-chain Attribute Authority, and blockchain-supported governance using Hyperledger Besu.

In addition to the integrated proof of concept, the repository also includes complementary ABE experiments used to evaluate cryptographic overhead, protected payload size, policy complexity, processing time, and accumulated overhead with real ESP32/DHT22 sensor measurements.

## Main Repository Components

### 1. Integrated Proof of Concept

**Path:** `integrated-poc/`

This directory contains the main proof-of-concept implementation of the proposed architecture. It validates the interaction among MQTT, OpenABE, ECIES, the Attribute Authority, subscriber-side key recovery, and the Hyperledger Besu blockchain layer.

Main subdirectories:

* `integrated-poc/attribute_authority/`
* `integrated-poc/contracts/`
* `integrated-poc/device_simulator/`
* `integrated-poc/producer_crypto/`
* `integrated-poc/subscriber_crypto/`
* `integrated-poc/shared/`
* `integrated-poc/scripts/`
* `integrated-poc/ui/`
* `integrated-poc/results/`
* `integrated-poc/docs/`

The integrated proof of concept supports both authorized and unauthorized access scenarios. In the authorized scenario, the subscriber attributes satisfy the access policy embedded in the CP-ABE ciphertext, allowing plaintext recovery. In the unauthorized scenario, the subscriber attributes do not satisfy the policy, and decryption fails as expected.

### 2. Smart Contract

**Path:** `integrated-poc/contracts/`

Main artifact:

* `AccessPolicyRegistryV3.sol`

The `AccessPolicyRegistryV3` smart contract is responsible for registering governance metadata related to the access-control workflow. Its role includes registering producers, consumers, topic policies, subscriber attributes, access requests, encrypted key grants, protected message metadata, integrity hashes, and consumption records.

The smart contract does not store plaintext sensor data and does not execute ABE cryptographic operations. Sensitive data remains off-chain, while the blockchain provides traceability and auditability for access-related events.

### 3. Attribute Authority

**Path:** `integrated-poc/attribute_authority/`

The Attribute Authority is an off-chain component responsible for processing access requests registered on the blockchain. It retrieves subscriber attributes, generates an OpenABE User Secret Key (USK) associated with those attributes, protects the generated key using ECIES, and registers the encrypted key grant on-chain.

The Attribute Authority does not make the final access decision through a conventional application-level conditional rule. In the adopted CP-ABE model, the final enforcement occurs during decryption: the protected payload can only be recovered when the attributes embedded in the USK satisfy the policy embedded in the ciphertext.

### 4. Producer-Side Cryptographic Module

**Path:** `integrated-poc/producer_crypto/`

This component receives IIoT sensor payloads, invokes the OpenABE-based CP-ABE workflow, encrypts the payload according to the access policy associated with the MQTT topic, and publishes the protected payload.

The producer-side cryptographic module keeps the MQTT broker from accessing plaintext data, since the broker only receives and routes protected payloads.

### 5. Subscriber-Side Cryptographic Module

**Path:** `integrated-poc/subscriber_crypto/`

This component retrieves the encrypted USK grant from the blockchain, decrypts it locally using the subscriber ECIES private key, verifies the integrity hash, restores the OpenABE key material, and attempts to decrypt the protected payload.

The subscriber-side module only recovers plaintext when the subscriber attributes satisfy the access policy associated with the CP-ABE ciphertext.

### 6. Streamlit Interface

**Path:** `integrated-poc/ui/`

The Streamlit interface provides a guided execution environment for the proof of concept. It centralizes the execution of the main scripts, displays logs and evidence files, and supports comparison between authorized and unauthorized scenarios.

The interface does not replace the technical scripts. Instead, it organizes the workflow to make the experiment easier to reproduce, inspect, and demonstrate.

### 7. Shared Utilities

**Path:** `integrated-poc/shared/`

This directory contains shared configuration and utility components used by different parts of the integrated proof of concept. These utilities support configuration management, cryptographic operations, Web3 interaction, MQTT parameters, topic definitions, and runtime paths.

### 8. Execution Scripts

**Path:** `integrated-poc/scripts/`

This directory contains the scripts used to execute the integrated workflow. The scripts support environment verification, on-chain bootstrap, MQTT sensor data collection, ABE encryption, access request creation, Attribute Authority processing, encrypted key retrieval, hash verification, and payload decryption.

The main validation flow includes:

1. checking the environment;
2. preparing the initial on-chain state;
3. collecting and protecting an MQTT sensor reading;
4. creating an access request;
5. processing the request through the Attribute Authority;
6. retrieving and decrypting the encrypted USK;
7. verifying the key integrity hash;
8. attempting CP-ABE decryption;
9. recording execution evidence.

### 9. ABE Experiments

**Path:** `abe-experiments/`

This directory contains complementary experiments focused on the cryptographic behavior and overhead of ABE-based protection.

Main subdirectories:

* `abe-experiments/scripts/`
* `abe-experiments/results/`
* `abe-experiments/docs/`

The experiments evaluate:

* encryption and decryption correctness;
* processing time;
* binary ABE ciphertext size;
* Base64-encoded ciphertext size;
* final ABE-protected payload size;
* spatial overhead by payload size;
* spatial overhead by access policy complexity;
* accumulated overhead using real ESP32/DHT22 sensor measurements.

These experiments support the quantitative analysis presented in the dissertation, especially regarding the trade-off between fine-grained access control and spatial overhead in small IIoT payloads.

### 10. Legacy and Supporting Components

**Paths:** `contracts/`, `orchestrator/`, `scripts/`, and infrastructure files in the project root.

Some directories in the repository correspond to earlier implementation stages or supporting infrastructure. For example, the root-level `contracts/` and `orchestrator/` directories were used in previous MQTT-blockchain integration experiments. They remain in the repository for historical traceability and implementation context, but the main integrated proof of concept is located in `integrated-poc/`.

The root-level infrastructure files, including Docker Compose and auxiliary scripts, support local execution and reproducibility of the experimental environment.

## Access to the Code

The source code can be accessed directly through the GitHub repository:

* [Repository main page](https://github.com/fiorezewesley/cross-org-iiot-security-blockchain)

Main integrated proof of concept:

* [Integrated PoC directory](https://github.com/fiorezewesley/cross-org-iiot-security-blockchain/tree/main/integrated-poc)

ABE experimental module:

* [ABE experiments directory](https://github.com/fiorezewesley/cross-org-iiot-security-blockchain/tree/main/abe-experiments)
