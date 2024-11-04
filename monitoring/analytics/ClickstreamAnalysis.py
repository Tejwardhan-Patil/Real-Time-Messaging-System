import json
import kafka
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
from collections import defaultdict
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window
from pyspark.sql.types import StructType, StringType, TimestampType

# Kafka Configuration
KAFKA_TOPIC = 'clickstream'
BOOTSTRAP_SERVERS = ['localhost:9092']
SPARK_APP_NAME = 'ClickstreamAnalysis'

# Initialize Kafka Consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='clickstream_group'
)

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Start Spark Session
spark = SparkSession.builder \
    .appName(SPARK_APP_NAME) \
    .getOrCreate()

# Schema for incoming data
clickstream_schema = StructType() \
    .add("user_id", StringType()) \
    .add("timestamp", TimestampType()) \
    .add("url", StringType()) \
    .add("referrer", StringType()) \
    .add("session_id", StringType()) \
    .add("event_type", StringType())

# Process incoming clickstream data
def process_clickstream_data(data):
    clicks = defaultdict(int)
    pages_visited = defaultdict(list)

    for record in data:
        user_id = record.get("user_id")
        timestamp = datetime.strptime(record.get("timestamp"), '%Y-%m-%dT%H:%M:%S.%fZ')
        url = record.get("url")
        event_type = record.get("event_type")

        clicks[user_id] += 1
        pages_visited[user_id].append(url)

    return clicks, pages_visited

# Function to analyze clickstream data
def analyze_clickstream(data):
    clicks, pages_visited = process_clickstream_data(data)
    
    for user, count in clicks.items():
        print(f"User {user} clicked {count} times.")
        print(f"Pages visited: {pages_visited[user]}")

# Kafka Stream to Spark Streaming DataFrame
clickstream_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", ",".join(BOOTSTRAP_SERVERS)) \
    .option("subscribe", KAFKA_TOPIC) \
    .load()

clickstream_df = clickstream_df \
    .selectExpr("CAST(value AS STRING)")

# Function to aggregate data
def aggregate_clickstream(df):
    return df \
        .groupBy(window(col("timestamp"), "1 minute"), col("url")) \
        .count()

# Real-time aggregation of clickstream events
def perform_realtime_analytics(df):
    agg_df = aggregate_clickstream(df)
    
    query = agg_df \
        .writeStream \
        .outputMode("complete") \
        .format("console") \
        .start()

    query.awaitTermination()

# Main Streaming Logic
def run_clickstream_analysis():
    # Deserialize JSON data from Kafka
    clickstream_data = clickstream_df \
        .selectExpr("CAST(value AS STRING) as json_data") \
        .withColumn("json_data", col("json_data").cast("string"))

    # Parse JSON to structured DataFrame
    parsed_df = spark.read \
        .json(clickstream_data.rdd.map(lambda r: r.json_data), schema=clickstream_schema)

    # Perform real-time analysis
    perform_realtime_analytics(parsed_df)

# Send analysis results to Kafka topic
def send_to_kafka(topic, message):
    producer.send(topic, message)
    producer.flush()

# Function to simulate data
def simulate_data():
    data = [
        {
            "user_id": "123",
            "timestamp": "2024-07-08T12:34:56.789Z",
            "url": "website.com/home",
            "referrer": "google.com",
            "session_id": "abc123",
            "event_type": "page_view"
        },
        {
            "user_id": "456",
            "timestamp": "2024-07-08T12:35:56.789Z",
            "url": "website.com/about",
            "referrer": "facebook.com",
            "session_id": "def456",
            "event_type": "page_view"
        }
    ]

    for event in data:
        send_to_kafka(KAFKA_TOPIC, event)

# Entry Point
if __name__ == "__main__":
    # Simulate some clickstream data
    simulate_data()

    # Run the analysis on incoming clickstream data
    run_clickstream_analysis()

    # Close Kafka connections
    producer.close()
    consumer.close()