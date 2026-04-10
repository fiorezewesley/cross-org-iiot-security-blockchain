# Experimental Results

## Overview

The current implementation provides an initial proof of concept of the proposed architecture for secure data sharing in Industrial Internet of Things (IIoT) environments.

The results demonstrate the successful integration between the MQTT communication layer, the Python orchestrator, and the blockchain layer based on Hyperledger Besu.

---

## 1. Blockchain Availability

The first validation step confirmed that the blockchain infrastructure is fully operational.

The following aspects were successfully verified:

- JSON-RPC endpoint accessible at `http://127.0.0.1:8545`  
- chain ID returned as `0x539` (1337 in decimal)  
- continuous block generation (`eth_blockNumber`)  
- ability to process and confirm transactions  

These observations indicate that the local Besu network is correctly configured and ready for experimental use.

---

## 2. Smart Contract Deployment

The smart contract `EncryptedDataRegistry` was successfully deployed to the local blockchain.

The deployment process produced the expected transaction receipt, including:

- transaction hash  
- block number  
- contract address  
- execution status (`status = 1`)  

Additionally, the contract was validated using JSON-RPC calls such as:

```text
eth_getCode
```

The presence of bytecode at the contract address confirms that the contract is correctly stored on-chain.

---

## 3. MQTT Communication Validation

The MQTT layer was validated using the Mosquitto broker.

The orchestrator successfully:

- connected to the MQTT broker  
- published test messages (`test/hello`)  
- subscribed to sensor topics (`sensors/#`)  
- received simulated sensor data  

These results confirm that the communication layer is functional and supports real-time message exchange.

---

## 4. End-to-End Integration

A complete end-to-end workflow was successfully executed.

The validated sequence is:

```text
MQTT → Orchestrator → Blockchain
```

The following steps were observed:

1. a simulated sensor message was published to an MQTT topic  
2. the orchestrator received and parsed the payload  
3. a SHA-256 hash was generated from the message content  
4. metadata (device ID, topic, policy, hash) was prepared  
5. a transaction was created and signed by the orchestrator  
6. the transaction was sent to the Besu node  
7. the transaction was mined and confirmed (`status = 1`)  
8. the event `RecordStored` was emitted by the smart contract  

This result demonstrates that the core architecture is functional.

---

## 5. Blockchain Event Validation

The transaction receipt confirmed the emission of the `RecordStored` event.

The receipt includes:

- contract address  
- event signature (topics)  
- encoded event data  
- block number and transaction index  

This provides a reliable audit trail for each recorded interaction.

---

## 6. Current Interpretation

At this stage, the prototype demonstrates:

- successful integration between off-chain and on-chain components  
- reliable transaction execution on a local blockchain  
- real-time message processing via MQTT  
- traceability of events through blockchain logs  
- preservation of confidentiality by keeping data off-chain  

---

## 7. Limitations

Despite the successful validation, the current implementation still presents limitations:

- the ABE module is not yet integrated into the main data flow  
- the `abePolicy` is currently a placeholder string  
- the hash represents the raw payload, not encrypted data  
- performance and scalability have not yet been evaluated  

These limitations define the next steps of the research.

---

## 8. Research Relevance

The obtained results are significant because they establish:

- a functional experimental baseline  
- a validated integration pipeline  
- a reproducible environment  

This foundation supports future work, particularly the integration of Attribute-Based Encryption (ABE) and the evaluation of access control mechanisms in multi-organizational IIoT scenarios.