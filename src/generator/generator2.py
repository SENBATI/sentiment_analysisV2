import json
import time
import random
import uuid
from datetime import datetime
from kafka import KafkaProducer

# --- CONFIGURATION ---
TOPIC_NAME = "social_posts"
BOOTSTRAP_SERVERS = ['localhost:9092']

# 1. Market Share (Weights)
# Bigger companies get more natural traffic
BRANDS_WEIGHTS = {
    "Maroc Telecom": 0.35,  # Dominant player
    "Orange Maroc": 0.25,
    "Inwi": 0.20,
    "Royal Air Maroc": 0.10,
    "BMCE Bank": 0.05,
    "Attijariwafa Bank": 0.05
}

# 2. Crisis Configuration
CRISIS_CHANCE = 0.05       # 5% chance to start a crisis each cycle
CRISIS_DURATION = 20       # Crisis lasts 20 cycles (approx 20 seconds)
IS_IN_CRISIS = False
CRISIS_BRAND = None
CRISIS_COUNTER = 0

TEMPLATES = {
    "positive": [
        "Excellent service de {brand} ! Bravo",
        "Très satisfait de {brand}, je recommande",
        "Merci {brand} pour votre professionnalisme",
        "Top expérience avec {brand} aujourd'hui"
    ],
    "neutral": [
        "Question pour {brand}: quelle offre ?",
        "Quelqu'un a testé {brand} ?",
        "Info: {brand} ouvre une agence à Casa",
        "Je viens de voir une pub pour {brand}"
    ],
    "negative": [
        "Service catastrophique de {brand}",
        "{brand} = pire expérience ever",
        "Encore une panne chez {brand} !",
        "Impossible de joindre le service client {brand}",
        "Vraiment déçu par {brand}..."
    ]
}

def get_producer():
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def generate_post(force_brand=None, force_sentiment=None):
    # 1. Pick a Brand (Weighted or Forced)
    if force_brand:
        brand = force_brand
    else:
        # Select brand based on market share weights
        brand = random.choices(
            list(BRANDS_WEIGHTS.keys()), 
            weights=list(BRANDS_WEIGHTS.values()), 
            k=1
        )[0]

    # 2. Pick Sentiment
    if force_sentiment:
        sentiment = force_sentiment
    else:
        # Normal distribution: Mostly neutral/positive
        rand = random.random()
        if rand < 0.6: sentiment = "neutral"
        elif rand < 0.9: sentiment = "positive"
        else: sentiment = "negative"

    # 3. Generate Content
    text = random.choice(TEMPLATES[sentiment]).format(brand=brand)

    return {
        "post_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "brand": brand,
        "source": random.choice(["Twitter", "Facebook", "Instagram"]),
        "text": text,
        "language": "fr"
    }

def main():
    producer = get_producer()
    global IS_IN_CRISIS, CRISIS_BRAND, CRISIS_COUNTER
    
    print(f"Generator V2.0 Started on {TOPIC_NAME}")
    print("   (Weighted Traffic + Random Crises)")

    try:
        while True:
            # --- LOGIC TO TRIGGER CRISIS ---
            if not IS_IN_CRISIS:
                if random.random() < CRISIS_CHANCE:
                    IS_IN_CRISIS = True
                    CRISIS_BRAND = random.choice(list(BRANDS_WEIGHTS.keys()))
                    CRISIS_COUNTER = CRISIS_DURATION
                    print(f"\n[!!!] STARTING SIMULATED CRISIS: {CRISIS_BRAND} [!!!]")

            # --- BATCH GENERATION ---
            batch_size = 30 if IS_IN_CRISIS else 10  # Traffic spikes during crisis
            
            for _ in range(batch_size):
                if IS_IN_CRISIS and random.random() < 0.8:
                    # 80% of traffic is the crisis brand with negative posts
                    post = generate_post(force_brand=CRISIS_BRAND, force_sentiment="negative")
                else:
                    # The rest is normal background noise
                    post = generate_post()
                
                producer.send(TOPIC_NAME, post)

            # --- STATE MANAGEMENT ---
            if IS_IN_CRISIS:
                print(f"Crisis active on {CRISIS_BRAND} ({CRISIS_COUNTER} left)")
                CRISIS_COUNTER -= 1
                if CRISIS_COUNTER <= 0:
                    IS_IN_CRISIS = False
                    print(f"[OK] Crisis ended for {CRISIS_BRAND}. Returning to normal.\n")
            else:
                print(".", end="", flush=True)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping producer.")
        producer.close()

if __name__ == "__main__":
    main()