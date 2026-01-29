import time
import json
import paho.mqtt.client as mqtt
import adafruit_dht
import board


# DHT11 CONFIGURATION

dht_device = adafruit_dht.DHT11(board.D17)  # GPIO17


# DITTO / MQTT CONFIG

THING_ID = "agriculture/CropTwin"
MQTT_TOPIC = f"{THING_ID}/things/twin/commands/modify"
SUBSCRIBE_TOPIC = f"{THING_ID}/things/twin/events/modified"

MQTT_BROKER = "192.168.1.100"   # Ditto on same Pi
MQTT_PORT = 1883
USERNAME = "ditto"
PASSWORD = "ditto"

# MQTT CALLBACKS

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    client.subscribe(SUBSCRIBE_TOPIC)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    print("Ditto event received:")
    print(payload)


# SEND DATA TO DITTO

def send_to_ditto(temperature, humidity):
    ditto_payload = {
        "topic": f"{THING_ID}/things/twin/commands/modify",
        "path": "/features/environmental_conditions/properties",
        "value": {
            "temperature": temperature,
            "humidity": humidity
        }
    }

    client.publish(MQTT_TOPIC, json.dumps(ditto_payload))
    print(f"Sent to Ditto → T={temperature}°C | H={humidity}%")


# MQTT CLIENT

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()


# MAIN LOOP

try:
    while True:
        temperature = dht_device.temperature
        humidity = dht_device.humidity

        if temperature is not None and humidity is not None:
            send_to_ditto(temperature, humidity)
        else:
            print("Sensor read failed")

        time.sleep(5)

except KeyboardInterrupt:
    print("Stopping...")
    client.loop_stop()
    client.disconnect()
    dht_device.exit()

