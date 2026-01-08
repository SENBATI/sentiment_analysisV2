# Social Sentinel: Real-Time Sentiment Analysis

- **Module:** Big Data Clusters & Distributed Systems
- **Year:** 2025/2026
- **Project Type:** Big Data Architecture with Kafka, Spark & Cassandra

---

## Project Overview

Social Sentinel is a complete Big Data architecture implementation (Kappa Architecture) for monitoring brand reputation and public sentiment across major Moroccan companies including Maroc Telecom, Orange, RAM, and others.

The system ingests real-time social media feeds, analyzes message sentiment (Positive/Negative/Neutral) using NLP, and triggers immediate alerts during crises (e.g., sudden satisfaction drops due to network outages or service issues).

### Key Features:

- **High-Frequency Ingestion:** Handles traffic spikes and burst loads efficiently
- **Low Latency:** Crisis detection in < 10 seconds
- **Real-Time Visualization:** Interactive web dashboard with Streamlit
- **Complete Storage:** Full historical data and temporal aggregations in Cassandra

---

## Technical Architecture

The data pipeline follows this workflow:

1. **Generator (Python):** Simulates realistic social media streams with weighted crisis scenarios
2. **Ingestion (Apache Kafka):** Buffers messages in `social_posts` topic (3 partitions)
3. **Stream Processing (Apache Spark Streaming):**
   - Micro-batch consumption
   - Data cleaning and Sentiment Analysis (TextBlob)
   - Sliding window aggregation (1-minute windows)
4. **Storage (Apache Cassandra):** Persists raw posts and aggregated metrics
5. **Visualization (Streamlit + Plotly):** Real-time monitoring interface with alert system

---

## Dashboard & Results

### 1. Normal Surveillance Mode

Real-time data flow visualization showing post volumes by brand and stable sentiment curves.

![Sentiment Evolution Curves](ressources/dashboard_normal_mode.png)

### 2. Crisis Detection

When a brand experiences a surge of negative comments, the system triggers visual red alerts and notifies operators within seconds.

![Crisis Detection - Reputation Drop](ressources/dashboard_crisis_mode.png)

### 3. Full Dashboard Overview

Complete dashboard interface showing all monitoring components.

![Complete Dashboard](ressources/dashboard_overview.png)

### 4. Data Storage Verification

Database view showing raw posts and associated sentiment scores, proving the write pipeline functions correctly.

![Cassandra Storage Proof](ressources/cassandra_storage.png)

---

## Installation & Quick Start

### Prerequisites

- Docker (for Kafka and Cassandra)
- Python 3.10+
- Java 11 (required for Spark)

### 1. Start Infrastructure

Ensure Docker containers are running:

```bash
# Start Cassandra
docker run --name cassandra -p 9042:9042 -d cassandra:4.1

# Verify Kafka and create topic if needed
docker exec -it kafka kafka-topics --create --topic social_posts --partitions 3 --bootstrap-server localhost:9092
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
python -m textblob.download_corpora
```

### 3. Run the Pipeline

Open 3 separate terminals and run commands in this order:

#### Terminal 1: Data Generator

```bash
python3 src/generator/post_generator.py
```

The script will send messages and periodically simulate random crises.

#### Terminal 2: Stream Processing Engine (Spark)

```bash
python3 src/processor/processor.py
```

Wait for JVM initialization and the "Streaming started" message.

#### Terminal 3: Web Dashboard

```bash
streamlit run src/dashboard/web_dashboard.py
```

The dashboard will open automatically in your browser at http://localhost:8501.

---

## Project Structure

```
crooked_version/
├── config/
│   └── cassandra_schema.cql         # Database schema
├── docs/                            # Documentation
├── ressources/                      # Screenshots and images
├── src/
│   ├── generator/
│   │   ├── generator2.py            # Data generator module
│   │   └── post_generator.py        # Traffic simulator (Normal + Crisis)
│   ├── processor/
│   │   └── processor.py             # Spark Streaming ETL pipeline
│   └── dashboard/
│       ├── dashboard.py             # Dashboard module
│       ├── dashboard2.py            # Alternative dashboard
│       └── web_dashboard.py         # Streamlit web interface
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
└── system_events.log                # Automatic crisis event logs
```

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Stream Ingestion | Apache Kafka | 2.x |
| Stream Processing | Apache Spark | 3.5.0 |
| Data Storage | Apache Cassandra | 4.1 |
| Sentiment Analysis | TextBlob | 0.17.1 |
| Web Framework | Streamlit | Latest |
| Data Processing | Pandas | 2.1.4 |
| NLP | NLTK | 3.8.1 |

---

## Challenges & Solutions

| Issue | Solution |
|-------|----------|
| **Spark/Java Compatibility:** Spark 3.5 required Java 11 | Set `JAVA_HOME` to OpenJDK 11 |
| **Cassandra Driver with Python 3.12:** C extension compilation errors | Install in pure Python mode (`CASSANDRA_DRIVER_NO_EXTENSIONS=1`) |
| **Kafka Legacy Support:** `kafka-python` compatibility issues | Upgraded dependencies for Python 3.10+ support |

---

## Usage Notes

- The generator creates realistic sentiment distributions with weighted crisis scenarios
- Crises trigger automatically with a 5% probability each cycle
- Crisis duration lasts approximately 20 seconds before sentiment returns to normal
- All events are logged to `system_events.log` for audit and analysis

---

## Author

Developed as part of the Big Data Clusters & Distributed Systems module for 2025/2026
