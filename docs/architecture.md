# System Architecture

## Architecture Overview

The proposed architecture integrates off-chain communication mechanisms with on-chain auditability to enable secure data sharing between multiple organizations in Industrial Internet of Things (IIoT) environments.

Considering the deterministic nature of smart contracts, computational performance limitations, and the need to preserve sensitive data, a mixed methodology was adopted. This approach ensures confidentiality without sacrificing traceability and auditability.

## Main Components

### 1. IIoT Devices

IIoT devices act as data producers within the system. They generate telemetry or operational data and publish messages to MQTT topics.

Example of a topic:

```text
sensors/sensor_001/data

```

These devices represent the origin of the information exchanged between organizations.

---

### 2. MQTT Broker (Eclipse Mosquitto)

The MQTT broker is responsible for implementing the publish/subscribe communication model.

Its role in the architecture includes:

- Decoupling data producers and consumers
- Enabling lightweight communication, suitable for IIoT
- Supporting near real-time message delivery

This component belongs entirely to the off-chain communication layer.

--

### 3. Python Orchestrator

The orchestrator is the central coordination component of the current prototype.

Your responsibilities include:

1. Connecting to the MQTT broker

2. Subscribing to sensor topics (`sensors/#`)

3. Receiving incoming messages

4. Extracting relevant metadata (e.g., device identifier and topic)

5. Generating a SHA-256 hash of the message content

6. Associating a policy marker for future integration with ABE

7. Sending a transaction to the blockchain smart contract

The orchestrator acts as the bridge between the off-chain communication layer and the on-chain audit layer.

---

### 4. Hyperledger Besu (Blockchain Layer)

Hyperledger Besu provides an Ethereum-compatible execution environment.

In this architecture, Besu is responsible for:

- registering devices
- distributing cryptographic keys for data access
- providing auditability through event logs

The current implementation uses a local development network exposed via JSON-RPC.

---

### 5. Smart Contract: EncryptedDataRegistry

The smart contract is responsible for storing metadata related to IIoT messages.

The current interface includes:

- `storeRecord()` — stores a new metadata record
- `getRecord()` — retrieves the stored data
- `lastId()` — returns the last stored record identifier

The contract also emits the event:

- `RecordStored` — used for traceability and auditing

The contract does not store raw sensor data. Instead, it stores metadata and a cryptographic hash, preserving confidentiality and ensuring integrity.

---

## Data Flow

The validated flow of the current prototype is:

```text
IIoT Device → MQTT Broker → Python Orchestrator → Hyperledger Besu```

## Security-Oriented Design Principles

The architecture follows fundamental security principles:

- **Confidentiality:** sensitive data remains off the blockchain
- **Integrity:** guaranteed through cryptographic hashing (SHA-256)
- **Traceability:** guaranteed through transaction logs on the blockchain
- **Auditability:** all interactions are recorded on the blockchain
- **Modularity:** allows for future integration of cryptographic components

---

## Integration of ABE

Attribute-Based Cryptography (ABE) will be integrated as a future enhancement.

Its objective will be:

- to enforce granular access control
- to allow only authorized entities to decrypt data
- to enable attribute-driven data sharing between organizations

The ABE module is being developed and tested separately and will be integrated into the orchestration layer later.

---
