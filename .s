import json
import time
import random
import uuid
from datetime import datetime
from kafka import KafkaProducer

# --- CONFIGURATION ---
TOPIC_NAME = "social_posts"
BOOTSTRAP_SERVERS = ['localhost:9092']  # Using localhost since you are running outside Docker
BRANDS = ["Maroc Telecom", "Orange Maroc", "Inwi", "Royal Air Maroc", "BMCE Bank", "Attijariwafa Bank"]

# Templates based on PDF scenarios
TEMPLATES = {
    "positive": [
        "Excellent service de {brand} ! Bravo",
        "Très satisfait de {brand}, je recommande",
        "Merci {brand} pour votre professionnalisme"
    ],
    "neutral": [
        "Question pour {brand}: quelle offre ?",
        "Quelqu'un a testé {brand} ?",
        "Info: {brand} ouvre une agence à Casa"
    ],
    "negative": [
        "Service catastrophique de {brand}",
        "{brand} = pire expérience ever",
        "Encore une panne chez {brand} !"
    ]
}

def get_producer():
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def generate_post():
    # 70% Neutral, 20% Positive, 10% Negative (Normal Scenario)
    rand = random.random()
    if rand < 0.7: sentiment = "neutral"
    elif rand < 0.9: sentiment = "positive"
    else: sentiment = "negative"

    brand = random.choice(BRANDS)
    text = random.choice(TEMPLATES[sentiment]).format(brand=brand)

    return {
        "post_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(), # ISO format for Spark
        "brand": brand,
        "source": random.choice(["Twitter", "Facebook"]),
        "text": text,
        "language": "fr"
    }

if __name__ == "__main__":
    producer = get_producer()
    print(f"Sending stream to {TOPIC_NAME}...")
    
    try:
        while True:
            for _ in range(10): # Burst of 10 messages
                post = generate_post()
                producer.send(TOPIC_NAME, post)
            
            time.sleep(1) # Wait 1 sec (Total ~10 posts/sec)
            print(".", end="", flush=True)
            
    except KeyboardInterrupt:
        print("\nStopping producer.")
        producer.close()