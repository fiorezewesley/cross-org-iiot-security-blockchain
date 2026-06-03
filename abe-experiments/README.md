# ABE Experiments for IIoT Sensor Payload Protection

This directory contains the experimental Attribute-Based Encryption (ABE) module used to evaluate cryptographic protection over Industrial Internet of Things (IIoT) sensor payloads.

The experiments complement the MQTT-blockchain integration prototype available in the main repository. At the current stage, this repository contains two complementary experimental layers:

1. an MQTT-blockchain integration prototype, based on MQTT, Python orchestration, and Hyperledger Besu;
2. an ABE-based experimental module for evaluating encryption, decryption, and overhead over simulated and real IIoT sensor payloads.

The ABE experiments are not presented as a fully integrated end-to-end pipeline with the blockchain layer. Instead, they provide an isolated and reproducible evaluation of the cryptographic component that supports the proposed architecture.

## Purpose

The purpose of these experiments is to evaluate the feasibility and cost of applying Attribute-Based Encryption to IIoT sensor data before sharing it across organizational boundaries.

The evaluation focuses on:

- encryption and decryption correctness;
- processing overhead;
- ciphertext size expansion;
- MQTT protected message overhead;
- access policy complexity;
- message volume using real sensor payloads.

## Directory Structure

    abe-experiments/
    ├── scripts/
    │   ├── producerside-abe-encrypt-module.py
    │   ├── subscriberside-abe-decrypt-module.py
    │   ├── subscriber_protected.py
    │   ├── exp1_overhead_payload_size.py
    │   ├── exp2_policy_complexity_overhead.py
    │   └── exp3_message_volume_real_sensor.py
    ├── results/
    │   ├── exp1_overhead_payload_size_20260524_173431.csv
    │   ├── exp2_policy_complexity_overhead_20260524_175913.csv
    │   ├── exp3_message_volume_real_sensor_details_20260524_193738.csv
    │   └── exp3_message_volume_real_sensor_summary_20260524_193738.csv
    └── docs/
        └── real_sensor_test_procedure.md

## Experimental Setup

The experiments were executed using OpenABE inside a Docker container. The Python scripts interact with OpenABE command-line routines through `docker exec`.

Default OpenABE container name:

    openabe-lab-split-test

The experiments use a CP-ABE setup and generate user secret keys according to the attributes required by each experiment.

Default library path used inside the container:

    /openabe/deps/root/lib:/openabe/root/lib:/usr/local/lib:$LD_LIBRARY_PATH

## Experiment 1 - Payload Size Overhead

Script:

    abe-experiments/scripts/exp1_overhead_payload_size.py

This experiment evaluates how the size of the original payload affects the size of the protected data.

It uses:

- one baseline sensor payload with temperature and humidity;
- synthetic JSON payloads with controlled sizes;
- a fixed access policy;
- repeated executions for each payload size.

Measured fields include:

- plaintext size;
- ciphertext binary size;
- ciphertext encoded in Base64;
- MQTT protected message size;
- encryption time;
- decryption time;
- decryption success;
- ciphertext overhead ratio;
- MQTT message overhead ratio.

Output file:

    abe-experiments/results/exp1_overhead_payload_size_20260524_173431.csv

## Experiment 2 - Access Policy Complexity Overhead

Script:

    abe-experiments/scripts/exp2_policy_complexity_overhead.py

This experiment isolates the impact of access policy complexity by keeping the payload size fixed and varying the number of attributes in the ABE policy.

The experiment uses:

- a fixed JSON payload size;
- policies with an increasing number of attributes;
- compatible user secret keys;
- repeated executions for each policy configuration.

The goal is to evaluate how the number of attributes affects encryption/decryption processing time and protected message size.

Output file:

    abe-experiments/results/exp2_policy_complexity_overhead_20260524_175913.csv

## Experiment 3 - Message Volume with Real Sensor Data

Script:

    abe-experiments/scripts/exp3_message_volume_real_sensor.py

This experiment evaluates the cryptographic protection of real sensor payloads received through MQTT.

Default topics:

    Input topic:  sala/sensor
    Output topic: sala/sensor/ciphertext/exp3

The script subscribes to the input topic, receives real sensor messages, normalizes the JSON payload, encrypts the payload using ABE, publishes the protected message to a dedicated MQTT topic, attempts decryption, and records detailed and summarized results.

Evaluated message volumes:

    30, 60, and 120 messages

Output files:

    abe-experiments/results/exp3_message_volume_real_sensor_details_20260524_193738.csv
    abe-experiments/results/exp3_message_volume_real_sensor_summary_20260524_193738.csv

## Running the Experiments

Start the OpenABE container:

    docker start openabe-lab-split-test

Activate the Python virtual environment:

    source .venv/bin/activate

Run each experiment from the repository root:

    python abe-experiments/scripts/exp1_overhead_payload_size.py
    python abe-experiments/scripts/exp2_policy_complexity_overhead.py
    python abe-experiments/scripts/exp3_message_volume_real_sensor.py

For Experiment 3, the MQTT broker must be running and the real sensor must be publishing JSON messages to:

    sala/sensor

The sensor can be monitored with:

    mosquitto_sub -h localhost -t "sala/sensor" -v

## Interpretation of Results

The CSV files provide quantitative evidence for evaluating the feasibility of using ABE to protect IIoT sensor data.

The most relevant metrics are:

- `plaintext_bytes`: original payload size;
- `ciphertext_bin_bytes`: binary ciphertext size;
- `ciphertext_b64_bytes`: Base64-encoded ciphertext size;
- `mqtt_message_bytes`: protected MQTT message size;
- `overhead_ciphertext_ratio`: ciphertext size divided by plaintext size;
- `overhead_mqtt_ratio`: protected MQTT message size divided by plaintext size;
- `overhead_mqtt_percentage`: percentage increase compared to the plaintext;
- `encryption_time_ms`: encryption time in milliseconds;
- `decryption_time_ms`: decryption time in milliseconds;
- `decrypt_success`: whether the original payload was correctly recovered.

## Scope and Limitations

These experiments evaluate the ABE component independently from the blockchain integration layer.

The current implementation demonstrates that IIoT sensor payloads can be encrypted and decrypted using attribute-based access policies, and that the resulting overhead can be measured in terms of processing time and message size.

The complete end-to-end integration among MQTT, ABE, and blockchain is part of the broader architecture and can be implemented as a subsequent development step.

## Relationship with the Dissertation Prototype

The main repository presents the architectural prototype for secure cross-organizational IIoT data sharing using MQTT, Hyperledger Besu, Python orchestration, and blockchain-based auditability.

This ABE module supports the security layer of the proposed architecture by experimentally evaluating data-centric access control. In this approach, access is not granted only by communication channel or identity, but by attributes associated with the consuming entity.

Therefore, these experiments provide evidence for the cryptographic feasibility of protecting IIoT payloads before they are shared among different organizations.
