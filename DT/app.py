from flask import Flask
from confluent_kafka import Consumer, Producer, KafkaException
import joblib
import json
import threading

# Load trained model
model = joblib.load('randomforest_model.pkl')

# Initialize Flask app
app = Flask(__name__)

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
INPUT_TOPIC = '_/_/things/twin/events'  # ← Use default topic instead of custom one
OUTPUT_TOPIC = 'flask-to-ditto'

# Set up Kafka Consumer config
consumer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'crop-prediction-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
}

# Set up Kafka Producer config
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
}

def delivery_report(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def parse_ditto_event(payload):
    """Extract soil_nutrients and environmental_conditions from Ditto event"""
    try:
        thing_value = payload.get('value', {})
        features = thing_value.get('features', {})

        soil_nutrients = features.get('soil_nutrients', {}).get('properties', {}).get('value', {})
        env_conditions = features.get('environmental_conditions', {}).get('properties', {}).get('value', {})

        return {
            'N': soil_nutrients.get('N'),
            'P': soil_nutrients.get('P'),
            'K': soil_nutrients.get('K'),
            'temperature': env_conditions.get('temperature'),
            'humidity': env_conditions.get('humidity'),
            'ph': env_conditions.get('ph'),
            'rainfall': env_conditions.get('rainfall')
        }
    except Exception as e:
        print("Error parsing Ditto event:", e)
        return None

def consume_and_predict():
    consumer = Consumer(consumer_conf)
    try:
        consumer.subscribe([INPUT_TOPIC])
        print("Consumer started. Waiting for messages...")

        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if 'PARTITION_EOF' in msg.error().str():
                    continue
                else:
                    raise KafkaException(msg.error())

            try:
                payload = json.loads(msg.value().decode('utf-8'))

                # Extract relevant data
                parsed_data = parse_ditto_event(payload)
                if not parsed_data:
                    continue

                # Build feature vector
                features = [
                    parsed_data['N'],
                    parsed_data['P'],
                    parsed_data['K'],
                    parsed_data['temperature'],
                    parsed_data['humidity'],
                    parsed_data['ph'],
                    parsed_data['rainfall']
                ]

                # Make prediction
                predicted_crop = model.predict([features])[0]
                print(f"Predicted Crop: {predicted_crop}")

                # Prepare response to update recommended_crop in Ditto
                thing_id = payload.get('topic', '').replace('/', ':')  # agriculture/CropTwin → agriculture:CropTwin

                response = {
                    "topic": thing_id,
                    "path": "/features/recommendation/value",
                    "value": {"recommended_crop": predicted_crop},
                    "headers": {
                        "content-type": "application/json"
                    }
                }

                # Send result back to Kafka
                producer = Producer(producer_conf)
                producer.produce(
                    OUTPUT_TOPIC,
                    value=json.dumps(response),
                    callback=delivery_report
                )
                producer.poll(0)
                producer.flush()

            except Exception as e:
                print(f"Error processing message: {e}")

    except KeyboardInterrupt:
        print("Stopping consumer...")
    finally:
        consumer.close()

@app.route('/')
def index():
    return "Crop Prediction Service Running"

if __name__ == '__main__':
    # Run Kafka consumer in background
    consumer_thread = threading.Thread(target=consume_and_predict, daemon=True)
    consumer_thread.start()

    # Run Flask API (for future use)
    app.run(host='0.0.0.0', port=5000)