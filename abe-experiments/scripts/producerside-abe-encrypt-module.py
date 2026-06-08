import base64
import json
import os
import subprocess
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883

INPUT_TOPIC = "sala/sensor"
OUTPUT_TOPIC = "sala/sensor/ciphertext"

OPENABE_CONTAINER = "openabe-lab-split-test"
LD_PATH = "/openabe/deps/root/lib:/openabe/root/lib:/usr/local/lib:$LD_LIBRARY_PATH"

def run_encrypt(payload: str, policy: str) -> str:
    cmd_encrypt = [
        "docker", "exec",
        "-e", f"OPENABE_MSG={payload}",
        "-e", f"OPENABE_POLICY={policy}",
        OPENABE_CONTAINER,
        "bash", "-lc",
        f"cd /openabe/examples && export LD_LIBRARY_PATH={LD_PATH} && ./cpabe_split encrypt"
    ]

    result = subprocess.run(cmd_encrypt, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    print("[producer-side] saída do OpenABE encrypt:")
    print(result.stdout.strip())

    cmd_read_ciphertext = [
        "docker", "exec",
        OPENABE_CONTAINER,
        "bash", "-lc",
        "base64 -w 0 /openabe/examples/state/ciphertext.bin"
    ]

    ct_result = subprocess.run(cmd_read_ciphertext, capture_output=True, text=True)

    if ct_result.returncode != 0:
        raise RuntimeError(ct_result.stderr.strip() or ct_result.stdout.strip())

    return ct_result.stdout.strip()

def on_connect(client, userdata, flags, rc):
    print(f"[producer-side] conectado ao MQTT rc={rc}")
    client.subscribe(INPUT_TOPIC)
    print(f"[producer-side] inscrito em {INPUT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8").strip()
        print(f"\n[producer-side] recebido do sensor: {payload}")

        parsed = json.loads(payload)
        normalized = json.dumps(parsed, separators=(",", ":"))

        policy = os.getenv("ABE_POLICY", "attr1 or attr2")

        ciphertext_b64 = run_encrypt(normalized, policy)

        protected_message = {
            "status": "encrypted",
            "policy": policy,
            "ciphertext_b64": ciphertext_b64
        }

        client.publish(OUTPUT_TOPIC, json.dumps(protected_message))
        print(f"[producer-side] ciphertext publicado em {OUTPUT_TOPIC}")

    except Exception as e:
        print(f"[producer-side] erro: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()