# Multi-Organizational IIoT Data Sharing Using ABE and Blockchain

## Overview

This website presents the technical documentation of a prototype master's thesis focused on data interoperability and privacy in Industrial Internet of Things (IIoT) environments.

The proposed architecture integrates off-chain communication mechanisms with on-chain auditability to enable secure data sharing between multiple organizations in Industrial Internet of Things (IIoT) environments.

Considering the deterministic nature of smart contracts, the limitations of computational performance, and the need to preserve sensitive data, a mixed methodology was adopted. This approach ensures confidentiality without sacrificing traceability and auditability.

## Current Implementation

At the current stage, the repository includes two complementary experimental layers:

- a MQTT-blockchain integration prototype using Hyperledger Besu, Eclipse Mosquitto, a Python orchestrator, and a Solidity smart contract;
- an isolated Attribute-Based Encryption (ABE) experimental module for evaluating cryptographic protection over IIoT sensor payloads.

## Architecture Layers

The system is structured in four conceptual layers:

- **Device Layer:** IIoT sensors that generate data
- **Communication Layer:** MQTT broker (Mosquitto)
- **Coordination Layer:** Python orchestrator
- **Audit Layer:** Hyperledger Besu for blockchain-based metadata registration

The ABE module is evaluated as an independent experimental security component. It is used to analyze encryption and decryption correctness, processing overhead, ciphertext expansion, MQTT protected message overhead, policy complexity, and message volume with simulated and real sensor data.

## Navigation

- [System Architecture](architecture.md)
- [Experimental Environment](experimental-environment.md)
- [Experimental Results](results.md)
- [Test](tests.md)
- [Source Code](code.md)

## Contribution

This prototype demonstrates a functional integration between distributed messaging systems and blockchain-based auditability mechanisms.

It also includes an experimental ABE module that evaluates data-centric access control for IIoT sensor payloads. The ABE experiments complement the main prototype by providing evidence on cryptographic overhead, ciphertext size expansion, policy complexity, and real sensor message volume.

The current repository should not be interpreted as a fully integrated end-to-end MQTT-ABE-blockchain implementation. The complete integration among these components is part of the broader proposed architecture and can be implemented as a subsequent development step.