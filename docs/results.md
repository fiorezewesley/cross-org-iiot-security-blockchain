# Experimental Results

## Overview

The current implementation provides an integrated proof of concept of the proposed architecture for secure cross-organizational data sharing in Industrial Internet of Things (IIoT) environments.

The results demonstrate the interaction among MQTT-based sensor data collection, CP-ABE payload protection using OpenABE, ECIES-protected key delivery, an off-chain Attribute Authority, subscriber-side key recovery, and blockchain-supported governance records using Hyperledger Besu.

In addition to the integrated proof of concept, the repository includes complementary ABE experiments used to evaluate cryptographic correctness, processing time, ciphertext expansion, protected payload size, policy complexity, and accumulated overhead with real ESP32/DHT22 sensor measurements.

---

## 1. Blockchain Availability

The first validation step confirmed that the local Hyperledger Besu blockchain infrastructure was operational.

The following aspects were verified:

* JSON-RPC endpoint accessible at `http://127.0.0.1:8545`;
* chain ID returned as `1337`;
* ability to deploy and interact with smart contracts;
* ability to process and confirm transactions;
* availability of event logs for access-related records.

These observations indicate that the local Besu network was correctly configured for the experimental validation of the proposed architecture.

---

## 2. Smart Contract Validation

The integrated proof of concept uses the smart contract `AccessPolicyRegistryV3` as the on-chain governance component.

The contract was used to register and retrieve metadata associated with the access-control workflow, including:

* producer and consumer devices;
* protected MQTT topics;
* access policies;
* subscriber attributes;
* access requests;
* encrypted key grants;
* integrity hashes;
* protected message metadata;
* consumption records and audit events.

The smart contract does not store plaintext sensor data and does not execute ABE cryptographic operations. Its role is to provide traceability and coordination for access-related metadata, while sensitive data and cryptographic operations remain off-chain.

---

## 3. MQTT Sensor Data Collection

The MQTT communication layer was validated using an Eclipse Mosquitto broker.

In the integrated proof of concept, an ESP32 device connected to a DHT22 sensor published temperature and humidity readings to a plaintext MQTT topic, such as:

`sensors/sensor_001/plain`

The producer-side cryptographic component received the sensor payload, normalized the message, and invoked the OpenABE-based CP-ABE encryption workflow. The resulting protected payload was then published to a protected MQTT topic, such as:

`sensors/sensor_001/protected`

These results confirm that the communication layer was able to support the sensor data flow required by the proposed architecture.

---

## 4. Integrated Proof-of-Concept Workflow

The integrated workflow validated the interaction among MQTT, OpenABE, ECIES, the Attribute Authority, subscriber-side key recovery, and Hyperledger Besu.

The validated execution flow can be summarized as follows:

1. the environment is checked, including the Besu RPC endpoint, deployed contract, OpenABE container, ECIES keys, topic policy, and subscriber attributes;
2. the initial on-chain state is prepared by registering the producer, subscriber, subscriber attributes, and topic access policy;
3. a real or controlled MQTT sensor reading is collected;
4. the producer-side cryptographic module encrypts the payload using CP-ABE according to the access policy;
5. the protected payload is published to the MQTT broker;
6. the subscriber creates an access request on the blockchain;
7. the off-chain Attribute Authority processes the access request;
8. the Attribute Authority generates an OpenABE User Secret Key associated with the subscriber attributes;
9. the generated USK is protected using ECIES with the subscriber public key;
10. the encrypted key grant and its integrity hash are registered on-chain;
11. the subscriber-side cryptographic module retrieves the encrypted key grant;
12. the subscriber decrypts the protected USK locally using its ECIES private key;
13. the integrity hash is verified against the value recorded on the blockchain;
14. the recovered OpenABE key material is restored;
15. CP-ABE decryption is attempted;
16. the plaintext is recovered only when the subscriber attributes satisfy the access policy embedded in the ciphertext.

This execution demonstrates that the architecture operates as an integrated end-to-end workflow in the evaluated local environment.

---

## 5. Access-Control Validation

The access-control behavior was validated using authorized and unauthorized subscriber attribute configurations.

In the authorized scenario, the access policy was defined as:

`attr1 or attr2`

and the subscriber attributes included:

`|attr1`

Since the subscriber attributes satisfied the policy, the protected payload was successfully decrypted and the original sensor reading was recovered.

In the unauthorized scenario, the subscriber attributes were set to:

`|attr3`

Since this attribute did not satisfy the policy `attr1 or attr2`, the OpenABE decryption process failed as expected.

These results confirm that the final access enforcement occurs at the CP-ABE decryption stage. The Attribute Authority issues a key associated with the registered subscriber attributes, while the actual access decision depends on whether those attributes satisfy the policy embedded in the ciphertext.

---

## 6. ECIES-Protected Key Delivery

The integrated proof of concept also validated the protection of OpenABE User Secret Keys during the key grant workflow.

The Attribute Authority generated an OpenABE USK associated with the subscriber attributes. Instead of storing this key in plaintext on-chain, the key artifact was protected using ECIES with the subscriber public key.

The encrypted key grant, referred to as `encUSK`, was registered on-chain together with an integrity hash. On the subscriber side, the encrypted key grant was retrieved, decrypted locally, and verified against the hash recorded on the blockchain.

The validation confirmed that:

* the OpenABE USK was not exposed in plaintext on-chain;
* the subscriber could recover the USK only through its ECIES private key;
* the integrity hash was correctly verified;
* the recovered key could be used in the subsequent CP-ABE decryption step.

This result reinforces the separation between blockchain-based auditability and off-chain protection of sensitive cryptographic material.

---

## 7. Streamlit Demonstration Interface

A Streamlit-based interface was implemented to organize the execution of the proof of concept into a reproducible workflow.

The interface supports:

* environment verification;
* preparation of the initial on-chain state;
* MQTT sensor data collection;
* access request creation;
* Attribute Authority processing;
* encrypted key retrieval;
* hash verification;
* CP-ABE decryption;
* visualization of logs and runtime evidence;
* comparison between authorized and unauthorized scenarios.

The interface does not replace the technical scripts used by the prototype. Instead, it centralizes their execution and makes the validation process easier to inspect and demonstrate.

---

## 8. ABE Overhead Evaluation

In addition to the integrated proof of concept, the repository includes ABE experiments focused on measuring cryptographic overhead.

The experiments evaluated:

* plaintext payload size;
* binary ABE ciphertext size;
* Base64-encoded ABE ciphertext size;
* final ABE-protected payload size;
* overhead ratio;
* overhead percentage;
* encryption time;
* decryption time;
* decryption success status.

The experiments were executed using OpenABE and controlled Python scripts that invoked the containerized cryptographic module and stored the resulting metrics in CSV files.

---

## 9. Spatial Overhead by Payload Size

The first overhead experiment evaluated how plaintext payload size affects the final ABE-protected payload size.

The evaluated payloads included one real sensor baseline payload and controlled JSON payloads with sizes of 32, 64, 128, 256, 512, 1024, 2048, and 4096 bytes.

The results showed that the ABE-protected payload was larger than the original plaintext in all evaluated cases. This effect was proportionally more significant for small payloads, because the cryptographic structures, Base64 encoding, access policy, and auxiliary metadata introduce overhead that becomes large when compared with small sensor measurements.

For the real sensor baseline:

* plaintext payload: 24 bytes;
* ABE-protected payload: 1049 bytes;
* overhead: 4270.83%.

For a 4096-byte payload, the relative overhead decreased to 102.47%. This reduction does not mean that the protected payload became smaller in absolute terms. Instead, it shows that the fixed part of the cryptographic and encoding overhead becomes proportionally less significant as the plaintext payload size increases.

---

## 10. Impact of Access Policy Complexity

The second experiment evaluated the impact of access policy complexity on protected payload size and processing time.

The plaintext payload size was fixed at 256 bytes, while the number of attributes in the access policy was varied. The evaluated policies contained 1, 2, 3, 4, 5, 10, 15, and 20 attributes.

The results showed that policy complexity directly affects spatial overhead. With one attribute, the protected payload had an average size of 1216 bytes, corresponding to an overhead of 375.00%. With 20 attributes, the protected payload reached an average size of 6069 bytes, corresponding to an overhead of 2270.70%.

This behavior is consistent with CP-ABE schemes, since the ciphertext structure includes components associated with the access policy. As the policy becomes more complex, more cryptographic material must be included in the ciphertext.

---

## 11. Accumulated Overhead with Real Sensor Measurements

The third experiment evaluated the accumulated overhead produced when real ESP32/DHT22 sensor measurements were protected individually.

The experiment evaluated three message volumes:

* 30 real sensor messages;
* 60 real sensor messages;
* 120 real sensor messages.

All 210 real sensor messages were successfully encrypted and decrypted. Each real sensor measurement had an average plaintext size of 24 bytes, while the corresponding ABE-protected payload had an average size of 1049 bytes.

The overhead percentage remained constant across the evaluated message volumes because both the accumulated plaintext size and the accumulated protected payload size increased proportionally. However, the total protected data volume accumulated linearly as each individual measurement generated a separate ABE-protected payload.

This result indicates that protecting each individual sensor measurement provides fine-grained confidentiality and access control, but may be inefficient in scenarios involving high-frequency sensing and very small payloads.

---

## 12. Processing Time

The experiments also measured the time required to invoke encryption and decryption operations.

In the payload-size evaluation, the average encryption time remained approximately between 65 ms and 74 ms, while the average decryption time remained approximately between 76 ms and 81 ms across the evaluated payload sizes.

In the policy-complexity evaluation, processing time increased as the number of attributes in the access policy grew. Encryption time varied from approximately 64.86 ms with one attribute to 105.58 ms with 20 attributes. Decryption time varied from approximately 82.47 ms to 146.38 ms.

In the real-sensor message evaluation, the average processing time remained stable across the evaluated message volumes. The average encryption time remained between approximately 74 ms and 77 ms per message, while the average decryption time remained between approximately 79 ms and 80 ms per message.

These results indicate that the proposed architecture is functionally viable in the evaluated local environment, but also show that applying ABE to each individual small measurement introduces measurable processing and spatial overhead.

---

## 13. Current Interpretation

The results demonstrate that the proposed architecture is viable within the evaluated scope.

The integrated proof of concept validated:

* MQTT-based IIoT sensor data collection;
* CP-ABE payload protection using OpenABE;
* blockchain-based registration of devices, attributes, topic policies, access requests, encrypted key grants, and hashes;
* ECIES-protected delivery of OpenABE User Secret Keys;
* subscriber-side key retrieval and integrity verification;
* authorized decryption when attributes satisfy the policy;
* unauthorized decryption failure when attributes do not satisfy the policy;
* execution support through a Streamlit interface.

The overhead experiments showed that ABE-based protection introduces relevant spatial overhead, especially for small IIoT payloads. They also showed that access policy complexity affects both protected payload size and processing time.

These results support the feasibility of combining MQTT-based IIoT communication, CP-ABE data-centric protection, ECIES-protected key delivery, and blockchain-supported governance for secure cross-organizational data sharing.

---

## 14. Limitations

Despite the successful validation, the current implementation still presents limitations:

* the experiments were conducted in a controlled local environment;
* system-level scalability with thousands of simultaneous devices was not evaluated;
* high-frequency distributed industrial workloads were not evaluated;
* multiple real organizations were not deployed in a distributed production setting;
* memory consumption during cryptographic operations was not directly measured;
* attribute revocation was discussed as an architectural challenge, but not implemented in the current prototype;
* large-scale industrial deployment remains future work.

These limitations do not invalidate the proof of concept. Instead, they define the boundaries of the current evaluation and indicate directions for future research.

---

## 15. Research Relevance

The obtained results are significant because they establish:

* a functional integrated proof of concept for secure IIoT data sharing;
* a validated workflow combining MQTT, CP-ABE, ECIES, Attribute Authority, and Hyperledger Besu;
* a reproducible local environment for academic evaluation;
* experimental evidence on cryptographic correctness and access enforcement;
* quantitative evidence on processing overhead, ciphertext expansion, protected payload size, policy complexity, and accumulated overhead with real sensor measurements;
* a technical artifact that supports future extensions and replication.

This foundation supports the proposed architecture for secure multi-organizational IIoT data sharing by combining blockchain-based auditability with data-centric access control through Attribute-Based Encryption.
