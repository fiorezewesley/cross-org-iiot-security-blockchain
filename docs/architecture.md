# System Architecture

## Architecture Overview

The proposed architecture integrates off-chain communication, data-centric cryptographic protection, and on-chain governance records to support secure data sharing between multiple organizations in Industrial Internet of Things (IIoT) environments.

The architecture follows a hybrid on-chain/off-chain design. Sensitive sensor data and Attribute-Based Encryption (ABE) cryptographic operations remain off-chain, while the blockchain layer is used to register governance metadata related to devices, attributes, topic policies, access requests, encrypted key grants, integrity hashes, and audit events.

This design avoids storing plaintext sensor data on the blockchain and prevents the blockchain from executing computationally expensive ABE operations. Instead, Hyperledger Besu and the `AccessPolicyRegistryV3` smart contract provide traceability and coordination for access-related records.

## Architecture Layers

The system is structured into two main layers:

* **Off-chain operational layer:** includes IIoT sensors, MQTT broker, producer-side and subscriber-side cryptographic frameworks, OpenABE-based CP-ABE operations, ECIES utilities, and the off-chain Attribute Authority.
* **On-chain governance layer:** implemented with Hyperledger Besu and the `AccessPolicyRegistryV3` smart contract, responsible for auditable access-related metadata.

The off-chain layer is responsible for data transmission, cryptographic protection, key handling, and plaintext recovery. The on-chain layer is responsible for recording and coordinating governance events without exposing sensitive data.

## Main Components

### 1. IIoT Devices

IIoT devices act as data producers or consumers within the system.

Producer devices generate telemetry or operational data, such as temperature and humidity measurements, and publish messages to MQTT topics. In the implemented proof of concept, an ESP32 device connected to a DHT22 sensor is used to generate real sensor readings.

Example of a plaintext MQTT topic:

```text
sensors/sensor_001/plain
```

After cryptographic protection, the protected payload is published to a protected topic, such as:

```text
sensors/sensor_001/protected
```

Resource-constrained sensors are not required to execute ABE operations directly. Instead, cryptographic operations are assigned to producer-side and subscriber-side cryptographic frameworks.

### 2. MQTT Broker

The MQTT broker implements the publish/subscribe communication model used by the IIoT data flow.

Its role includes:

* decoupling producers and consumers;
* supporting lightweight message delivery;
* routing protected payloads between the producer-side and subscriber-side components.

The MQTT broker does not perform authorization checks and does not enforce access decisions. It only transports protected payloads. Access control is enforced cryptographically through CP-ABE during the decryption process.

### 3. Producer-Side Cryptographic Framework

The producer-side cryptographic framework receives the sensor payload, retrieves or applies the access policy associated with the MQTT topic, and protects the payload using CP-ABE through OpenABE.

Its responsibilities include:

* receiving or collecting sensor measurements;
* normalizing the payload;
* applying the access policy associated with the protected topic;
* invoking the OpenABE-based CP-ABE encryption workflow;
* generating the ABE-protected payload;
* publishing the protected payload to the MQTT broker.

This component ensures that plaintext sensor data is protected before being transmitted through the MQTT broker.

### 4. Subscriber-Side Cryptographic Framework

The subscriber-side cryptographic framework is responsible for retrieving the encrypted User Secret Key (USK), verifying its integrity, restoring the OpenABE key material, and attempting to decrypt the protected payload.

Its responsibilities include:

* retrieving the encrypted key grant from the blockchain;
* decrypting the encrypted USK locally using the subscriber ECIES private key;
* verifying the integrity hash recorded on-chain;
* restoring the OpenABE user key;
* attempting CP-ABE decryption of the protected payload;
* returning plaintext only when the subscriber attributes satisfy the access policy embedded in the ciphertext.

The final access decision occurs during CP-ABE decryption. If the attributes associated with the subscriber key satisfy the policy, decryption succeeds. Otherwise, the protected data cannot be recovered.

### 5. Attribute Authority

The Attribute Authority is an off-chain component responsible for processing access requests and generating OpenABE User Secret Keys associated with subscriber attributes.

Its responsibilities include:

* observing or processing access requests registered on-chain;
* retrieving subscriber attributes registered in the smart contract;
* generating an OpenABE User Secret Key bound to the subscriber attributes;
* protecting the generated USK using ECIES with the subscriber public key;
* computing an integrity hash for the protected key artifact;
* registering the encrypted key grant and hash on the blockchain.

The Attribute Authority does not make the final access decision through a conventional application-level conditional rule. In the adopted CP-ABE model, the final enforcement occurs during decryption, according to the relationship between the attributes embedded in the USK and the access policy embedded in the ciphertext.

### 6. Hyperledger Besu

Hyperledger Besu provides the Ethereum-compatible blockchain layer used in the proposed architecture.

In this proof of concept, Besu is executed as a local development network and exposes a JSON-RPC interface for interaction with Python scripts and Web3.py.

Its role includes:

* supporting smart contract deployment and execution;
* recording device and attribute metadata;
* recording access policies associated with MQTT topics;
* registering access requests;
* storing encrypted key grant metadata;
* storing integrity hashes;
* providing auditable records of access-related events.

The blockchain layer does not store plaintext sensor data and does not execute ABE cryptographic operations.

### 7. Smart Contract: AccessPolicyRegistryV3

The main smart contract used in the integrated proof of concept is:

```text
AccessPolicyRegistryV3.sol
```

This contract is responsible for registering governance metadata associated with the access-control workflow.

Its role includes:

* registering producer and consumer devices;
* associating access policies with protected MQTT topics;
* registering subscriber attributes;
* creating access requests;
* storing encrypted key grants;
* storing integrity hashes;
* registering protected message metadata;
* registering consumption records and audit events.

The contract provides traceability and coordination for the access workflow, while sensitive cryptographic material remains protected off-chain.

## Integrated Data Flow

The validated integrated workflow can be summarized as follows:

```text
Sensor payload
→ Producer-side cryptographic framework
→ CP-ABE protected payload
→ MQTT broker
→ Subscriber-side cryptographic framework
→ Access request on Hyperledger Besu
→ Attribute Authority processing
→ ECIES-protected USK grant
→ Subscriber-side key retrieval and hash verification
→ CP-ABE decryption attempt
→ Plaintext recovery only when attributes satisfy the access policy
```

This flow demonstrates the integration of MQTT communication, CP-ABE payload protection, ECIES-based key delivery, off-chain Attribute Authority processing, and blockchain-supported governance records.

## Access-Control Workflow

The access-control workflow is organized into five main phases.

### 1. Registration and Policy Definition

The producer, subscriber, subscriber attributes, and topic access policy are registered on-chain through the smart contract.

The blockchain acts as an auditable registry for:

* devices;
* attributes;
* protected topics;
* access policies;
* governance events.

### 2. Sensor Data Protection

The producer-side cryptographic framework receives the sensor reading and encrypts the payload using CP-ABE according to the access policy associated with the protected topic.

The protected payload is then published through the MQTT broker.

### 3. Access Request

The subscriber creates an access request on the blockchain for a protected topic. This request does not provide direct access to plaintext data. It only creates an auditable request record to be processed by the Attribute Authority.

### 4. Key Grant Processing

The Attribute Authority processes the access request, retrieves the subscriber attributes, generates an OpenABE User Secret Key, protects this key using ECIES, computes an integrity hash, and registers the encrypted key grant on-chain.

### 5. Key Retrieval and Decryption

The subscriber-side cryptographic framework retrieves the encrypted key grant, decrypts it locally, verifies the integrity hash, restores the OpenABE key material, and attempts to decrypt the protected payload.

If the subscriber attributes satisfy the CP-ABE policy, the plaintext is recovered. If the attributes do not satisfy the policy, decryption fails.

## Security-Oriented Design Principles

The architecture follows the following security-oriented principles:

* **Confidentiality:** plaintext sensor data is kept off-chain and is protected before publication.
* **Data-centric access control:** access decisions are enforced through CP-ABE, independently of the MQTT broker.
* **Integrity:** key grant artifacts are verified using hashes recorded on-chain.
* **Auditability:** access requests, key grants, policies, and related events are registered on the blockchain.
* **Separation of responsibilities:** MQTT transports messages, CP-ABE enforces access control, ECIES protects key delivery, the Attribute Authority issues attribute-bound keys, and the blockchain records governance metadata.
* **Reduced exposure of sensitive key material:** the OpenABE User Secret Key is protected before being registered as an encrypted grant and is recovered only by the subscriber-side cryptographic framework.
* **Off-chain cryptographic execution:** computationally expensive ABE operations are not executed by the blockchain.

## Current Implementation Scope

The current implementation validates the proposed architecture in a controlled local environment. It includes:

* MQTT-based sensor data collection;
* CP-ABE payload protection using OpenABE;
* Hyperledger Besu blockchain records;
* the `AccessPolicyRegistryV3` smart contract;
* an off-chain Attribute Authority;
* ECIES-protected delivery of OpenABE User Secret Keys;
* subscriber-side key retrieval and integrity verification;
* successful and unsuccessful decryption scenarios according to ABE access policies;
* a Streamlit interface for guided execution and evidence inspection.

Large-scale distributed deployments involving multiple organizations, thousands of simultaneous devices, and high-frequency industrial workloads remain outside the current experimental scope and are considered future work.
