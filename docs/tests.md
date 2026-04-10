# Test Procedures

## Overview

This section describes the procedures used to validate the current prototype. The goal is to ensure that all components of the architecture are operational and that the end-to-end integration can be reproduced.

---

## 1. Starting the Infrastructure

The complete environment can be started using the provided script:

```bash
./scripts/01_start_infra.sh
```

Alternatively, the services can be started directly using Docker Compose:

```bash
docker compose up -d
```

---

## 2. Verifying Running Services

To confirm that all services are active:

```bash
docker compose ps
```

Expected containers:

- besu-node  
- mosquitto-broker  
- orchestrator  

---

## 3. Inspecting Orchestrator Logs

To verify that the orchestrator initialized correctly:

```bash
docker logs orchestrator --tail=80
```

Expected observations:

- attempts to connect to Besu  
- successful connection to the blockchain  
- successful connection to MQTT  
- subscription to `sensors/#`  
- initialization of message listener  

---

## 4. Testing Basic MQTT Communication

### Subscribe to test topic

```bash
mosquitto_sub -h localhost -p 1883 -t "test/hello" -v
```

### Restart orchestrator to trigger message

```bash
docker restart orchestrator
```

Expected result:

- a message published by the orchestrator appears in the subscriber terminal  

---

## 5. Simulating Sensor Data

To simulate a real IIoT message:

```bash
mosquitto_pub -h localhost -p 1883 \
-t "sensors/sensor_001/data" \
-m '{"sensor_id": "sensor_001", "temp": 23.7, "humidity": 60}'
```

---

## 6. Validating Message Processing

While publishing the message, monitor the orchestrator logs:

```bash
docker logs -f orchestrator
```

Expected behavior:

- message reception  
- payload parsing  
- metadata extraction  
- hash generation  
- transaction creation  

---

## 7. Validating Blockchain Connectivity

To confirm that the blockchain is accessible:

### Check chain ID

```bash
curl -s -X POST http://127.0.0.1:8545 \
-H "Content-Type: application/json" \
--data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```

Expected result:

```
0x539
```

---

### Check block progression

```bash
curl -s -X POST http://127.0.0.1:8545 \
-H "Content-Type: application/json" \
--data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

Expected behavior:

- increasing block number  

---

## 8. Validating Smart Contract Interaction

After publishing a sensor message, verify:

- a transaction was submitted  
- the transaction was mined  
- the receipt status is `1`  
- the `RecordStored` event was emitted  

This can be confirmed through:

- orchestrator logs  
- JSON-RPC calls (`eth_getTransactionReceipt`)  

---

## 9. Expected Outcome

A successful test execution should confirm:

- all services are running  
- MQTT communication is functional  
- the orchestrator processes incoming messages  
- a transaction is sent to the blockchain  
- the transaction is confirmed and recorded  
- a corresponding event is emitted  

---

## 10. Reproducibility

All steps described in this section can be repeated without modifying the environment configuration, ensuring that the experimental results are reproducible.