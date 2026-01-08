from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf, window, avg, count, when
from pyspark.sql.types import StringType, StructType, StructField, FloatType, TimestampType
from textblob import TextBlob

# --- CONFIGURATION ---
KAFKA_TOPIC = "social_posts"
KAFKA_BOOTSTRAP = "localhost:9092"
CASSANDRA_KEYSPACE = "social_media"
CASSANDRA_TABLE_POSTS = "posts"
CASSANDRA_TABLE_AGG = "sentiment_aggregates"

# Define Schema for Incoming Data
schema = StructType([
    StructField("post_id", StringType()),
    StructField("timestamp", TimestampType()),
    StructField("brand", StringType()),
    StructField("source", StringType()),
    StructField("text", StringType()),
    StructField("language", StringType())
])

# --- SENTIMENT FUNCTIONS ---
def get_sentiment_score(text):
    try:
        return float(TextBlob(text).sentiment.polarity)
    except:
        return 0.0

def get_sentiment_label(score):
    if score > 0.1: return "positive"
    elif score < -0.1: return "negative"
    else: return "neutral"

# Register UDFs (User Defined Functions)
sentiment_score_udf = udf(get_sentiment_score, FloatType())
sentiment_label_udf = udf(get_sentiment_label, StringType())

# --- MAIN ---
if __name__ == "__main__":
    # Initialize Spark with Kafka and Cassandra packages
    spark = SparkSession.builder \
        .appName("SentimentAnalysis") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.5.0") \
        .config("spark.cassandra.connection.host", "localhost") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # 1. READ STREAM (Kafka)
    df_raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    # 2. PARSE JSON
    df_parsed = df_raw.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    # 3. ENRICH (Sentiment Analysis)
    df_enriched = df_parsed \
        .withColumn("sentiment_score", sentiment_score_udf(col("text"))) \
        .withColumn("sentiment_label", sentiment_label_udf(col("sentiment_score")))

    # 4. AGGREGATE (1 Minute Windows)
    df_agg = df_enriched \
        .groupBy(
            window(col("timestamp"), "1 minute"),
            col("brand")
        ) \
        .agg(
            avg("sentiment_score").alias("avg_sentiment"),
            count("post_id").alias("post_count"),
            count(when(col("sentiment_label") == "positive", 1)).alias("positive_count"),
            count(when(col("sentiment_label") == "neutral", 1)).alias("neutral_count"),
            count(when(col("sentiment_label") == "negative", 1)).alias("negative_count")
        ) \
        .select(
            col("brand"),
            col("window.start").alias("window_start"),
            col("avg_sentiment"),
            col("post_count"),
            col("positive_count"),
            col("neutral_count"),
            col("negative_count")
        )

    # 5. WRITE STREAMS (Cassandra)
    
    # Write Raw Posts
    query_posts = df_enriched.writeStream \
        .trigger(processingTime='5 seconds') \
        .foreachBatch(lambda batch_df, batch_id: batch_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table=CASSANDRA_TABLE_POSTS, keyspace=CASSANDRA_KEYSPACE) \
            .save()) \
        .start()

    # Write Aggregates
    query_agg = df_agg.writeStream \
        .trigger(processingTime='1 minute') \
        .outputMode("update") \
        .foreachBatch(lambda batch_df, batch_id: batch_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table=CASSANDRA_TABLE_AGG, keyspace=CASSANDRA_KEYSPACE) \
            .save()) \
        .start()

    print(">>> Streaming started... Waiting for data...")
    spark.streams.awaitAnyTermination()