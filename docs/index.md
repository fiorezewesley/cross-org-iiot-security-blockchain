# Multi-Organizational IIoT Data Sharing Using ABE and Blockchain

## Overview

This website presents the technical documentation of a prototype master's thesis focused on data interoperability and privacy in Industrial Internet of Things (IIoT) environments.

The proposed architecture integrates off-chain communication mechanisms with on-chain auditability to enable secure data sharing between multiple organizations in Industrial Internet of Things (IIoT) environments.

Considering the deterministic nature of smart contracts, the limitations of computational performance, and the need to preserve sensitive data, a mixed methodology was adopted. This approach ensures confidentiality without sacrificing traceability and auditability.

## Current Implementation

At the current stage, the prototype integrates:

- Hyperledger Besu as a local blockchain network
- Eclipse Mosquitto as an MQTT broker
- a Python orchestrator for off-chain coordination
- a Solidity smart contract for on-chain metadata registration

## Architecture Layers

The system is structured in four conceptual layers:

- **Device Layer:** IIoT sensors that generate data
- **Communication Layer:** MQTT broker (Mosquitto)
- **Coordination Layer:** Python orchestrator
- **Audit Layer:** ABE and Hyperledger Besu (blockchain)

## Navigation

- [System Architecture](architecture.md)
- [Experimental Environment](experimental-environment.md)
- [Experimental Results](results.md)
- [Test](tests.md)
- [Source Code](code.md)

## Contribution

This prototype demonstrates a functional integration between distributed messaging systems and blockchain-based auditability mechanisms.

It serves as a proof of concept for IIoT interoperability across multiple organizations and establishes the basis for the future integration of a cryptographic ABE module for granular access control.