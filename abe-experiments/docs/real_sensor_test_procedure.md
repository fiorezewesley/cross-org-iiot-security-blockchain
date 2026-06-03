# Real Sensor Test Procedure

This document describes the practical procedure used to test Attribute-Based Encryption (ABE) with real sensor data published through MQTT.

The goal of this procedure is to validate the cryptographic protection of sensor payloads before data sharing. The test uses an ESP32 sensor publisher, a local MQTT broker, and an OpenABE Docker container.

## 1. Connect the ESP32 Sensor

Connect the ESP32 board through USB.

If the firmware is managed with PlatformIO in Visual Studio Code, upload the firmware to the ESP32 using the PlatformIO upload option.

The sensor is expected to publish JSON messages to the MQTT topic:

    sala/sensor

Example of expected payload:

    {"temp":24.90,"hum":77.10}

## 2. Verify Sensor Publication

Use mosquitto_sub to verify that the MQTT broker is receiving sensor data:

    mosquitto_sub -h localhost -t "sala/sensor" -v

If the sensor is working correctly, the terminal should display messages published to the sala/sensor topic.

## 3. Start the OpenABE Container

Start the OpenABE container used by the Python scripts:

    docker start openabe-lab-split-test

Optionally, open an interactive shell inside the container:

    docker exec -it openabe-lab-split-test bash

## 4. Activate the Python Virtual Environment

From the host machine, activate the Python virtual environment:

    source .venv/bin/activate

## 5. Run the Producer-Side ABE Module

In the first terminal, run:

    python abe-experiments/scripts/producerside-abe-encrypt-module.py

This module is responsible for preparing or receiving sensor payloads and applying ABE-based encryption according to the configured access policy.

## 6. Run the Subscriber-Side ABE Module

In a second terminal, activate the virtual environment again:

    source .venv/bin/activate

Then run:

    python abe-experiments/scripts/subscriberside-abe-decrypt-module.py

This module is responsible for consuming protected messages and attempting decryption using the available user attributes.

## 7. Run the Real Sensor Message Volume Experiment

To execute the real sensor message volume experiment, run:

    python abe-experiments/scripts/exp3_message_volume_real_sensor.py

The script subscribes to:

    sala/sensor

It publishes protected messages to:

    sala/sensor/ciphertext/exp3

The generated CSV files are stored in:

    abe-experiments/results/

## 8. Validate the Results

The most relevant validation field is:

    decrypt_success

A True value indicates that the encrypted payload was successfully decrypted and that the recovered output contains the original normalized sensor payload.

The summary CSV also reports:

- total collected messages;
- successful decryptions;
- failed decryptions;
- accumulated MQTT overhead;
- average encryption time;
- average decryption time;
- effective messages per second.

## 9. Notes on Scope

This procedure validates the ABE-based protection of real sensor payloads over MQTT.

The test does not represent the complete end-to-end integration among MQTT, ABE, and blockchain. Instead, it validates the cryptographic module that supports the proposed architecture.

The complete integration between the ABE module and the blockchain auditability layer is part of the broader architecture and can be implemented as a subsequent development step.
