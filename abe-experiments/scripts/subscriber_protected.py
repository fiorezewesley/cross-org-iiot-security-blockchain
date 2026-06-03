import json
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883
PROTECTED_TOPIC = "sala/sensor/openabe_cpabe"

def on_connect(client, userdata, flags, rc):
    print(f"[subscriber] conectado ao MQTT rc={rc}")
    client.subscribe(PROTECTED_TOPIC)
    print(f"[subscriber] inscrito em {PROTECTED_TOPIC}")

def on_message(client, userdata, msg):
    print("\n[subscriber] mensagem recebida no tópico protegido")
    print(f"[subscriber] tópico: {msg.topic}")

    payload = msg.payload.decode("utf-8", errors="replace")
    print("[subscriber] payload recebido:")
    print(payload)

    try:
        data = json.loads(payload)
        print("\n[subscriber] JSON interpretado:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        status = data.get("status")

        if status == "processed_by_abe_module":
            print("\n[subscriber] resultado: processamento criptográfico concluído com sucesso")

        elif status == "decryption_failed":
            print("\n[subscriber] resultado: falha esperada de descriptografia")
            print(f"[subscriber] política: {data.get('policy')}")
            print(f"[subscriber] atributos usados: {data.get('attrs')}")

        else:
            print("\n[subscriber] resultado: status não reconhecido")

    except Exception as e:
        print("[subscriber] payload não está em JSON válido")
        print(f"[subscriber] erro: {e}")

print("[subscriber] iniciando...")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"[subscriber] conectando em {MQTT_HOST}:{MQTT_PORT}")
client.connect(MQTT_HOST, MQTT_PORT, 60)

print("[subscriber] aguardando mensagens...")
client.loop_forever()