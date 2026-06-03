import json
import subprocess
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883

INPUT_TOPIC = "sala/sensor/ciphertext"

OPENABE_CONTAINER = "openabe-lab-split-test"
LD_PATH = "/openabe/deps/root/lib:/openabe/root/lib:/usr/local/lib:$LD_LIBRARY_PATH"

def write_ciphertext_to_container(ciphertext_b64: str) -> None:
    cmd = [
        "docker", "exec", "-i",
        OPENABE_CONTAINER,
        "bash", "-lc",
        "base64 -d > /openabe/examples/state/ciphertext.bin"
    ]

    result = subprocess.run(cmd, input=ciphertext_b64, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

def run_decrypt() -> str:
    cmd = [
        "docker", "exec",
        OPENABE_CONTAINER,
        "bash", "-lc",
        f"cd /openabe/examples && export LD_LIBRARY_PATH={LD_PATH} && ./cpabe_split decrypt"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    output = ""
    if result.stdout:
        output += result.stdout.strip()

    if result.stderr:
        output += "\n" + result.stderr.strip()

    if result.returncode != 0:
        raise RuntimeError(output.strip())

    return output.strip()

def on_connect(client, userdata, flags, rc):
    print(f"[subscriber-side] conectado ao MQTT rc={rc}")
    client.subscribe(INPUT_TOPIC)
    print(f"[subscriber-side] inscrito em {INPUT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8").strip()

        print("\n[subscriber-side] ciphertext recebido")
        print(f"[subscriber-side] tópico: {msg.topic}")

        data = json.loads(payload)

        if data.get("status") != "encrypted":
            print("[subscriber-side] mensagem ignorada: status diferente de encrypted")
            return

        policy = data.get("policy")
        ciphertext_b64 = data.get("ciphertext_b64")

        if not ciphertext_b64:
            print("[subscriber-side] ciphertext_b64 ausente")
            return

        print(f"[subscriber-side] política associada ao ciphertext: {policy}")

        write_ciphertext_to_container(ciphertext_b64)

        decrypt_output = run_decrypt()

        print("[subscriber-side] saída do OpenABE decrypt:")
        print(decrypt_output)

    except Exception as e:
        print("[subscriber-side] falha na descriptografia")
        print(e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()