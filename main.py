import streamlit as st
import pandas as pd
import json
from kafka import KafkaProducer, KafkaConsumer
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, DoubleType, StringType
from pyspark.sql.functions import lit, desc
from pyspark.ml import PipelineModel
import threading
import time

# Initialize Spark
spark = SparkSession \
    .builder \
    .appName("RecommendationSystem") \
    .master("local") \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.memory", "8g") \
    .getOrCreate()

# Initialize Kafka producer
producer = KafkaProducer(bootstrap_servers='localhost:9092')

# Initialize Kafka consumer
consumer = KafkaConsumer(
    'test',
    bootstrap_servers='localhost:9092',
    group_id='mygroup',
    auto_offset_reset='earliest'
)
consumer.subscribe(['test'])

# Function to process the received message
def process_message(message):
    value = message.value.decode('utf-8')
    st.sidebar.write("Message consumed:", value)

# Function to send Kafka messages
def send_message(message):
    producer.send('test', message.encode('utf-8'))
    producer.flush()

# Function to fetch recommendations using the ALS model
def fetch_recommendations(reviewer_id):
    # Load the saved ALS model
    path = "C:/Users/pc/Desktop/Spark_Project/ALS_model"
    loaded_model_mf = PipelineModel.load(path)

    # Load the input data for prediction
    csv_path = "C:/Users/pc/Desktop/Spark_Project/reviewer.csv"
    schema = StructType([StructField("asin", DoubleType(), nullable=True)])
    df = spark.read.csv(csv_path, header=True, schema=schema)

    # Prepare the data for the specified reviewer_id
    value = float(reviewer_id)
    final_df = df.withColumn("reviewer_id", lit(value))
    df = final_df.select("reviewer_id", "asin")
    final_df = df.withColumnRenamed("reviewer_id", "reviewerID_index").withColumnRenamed("asin", "asin_index")

    # Generate predictions using the ALS model
    user_predictions = loaded_model_mf.transform(final_df)

    # Sort predictions by descending score
    sorted_predictions = user_predictions.orderBy(desc("prediction"))

    # Select the top 5 results
    top_5_asin = sorted_predictions.select("asin_index").limit(5).collect()

    # Convert results into a readable format
    return {"top_5_asin": [{"asin_index": row.asin_index} for row in top_5_asin]}

# Function to consume messages from Kafka in the background
def consume_messages():
    for message in consumer:
        process_message(message)

# Start Kafka consumer in a background thread
def start_consumer():
    threading.Thread(target=consume_messages, daemon=True).start()

start_consumer()

# Streamlit interface
st.set_page_config(page_title="Product Recommendation System", page_icon="🛍️", layout="wide")
st.title("🎯 Fast Product Recommendation System")

# Sidebar: User input
st.sidebar.header("User Input")
reviewer_id = st.sidebar.number_input("Enter your Reviewer ID:", min_value=0, step=1)

# Get recommendations when button is clicked
if st.sidebar.button("Get Recommendations"):
    if reviewer_id is not None:
        # Get recommendations for the reviewer
        recommendations = fetch_recommendations(reviewer_id)

        # Display recommendations
        st.subheader("🔝 Top 5 Recommendations")
        st.write(pd.DataFrame(recommendations["top_5_asin"]))

        # Send recommendations to Kafka
        send_message(json.dumps(recommendations))
        st.sidebar.success("Recommendations sent to Kafka.")
    else:
        st.sidebar.error("Please enter a valid reviewer ID.")

# Sidebar: Kafka Streaming
st.sidebar.header("Kafka Streaming")
if st.sidebar.button("Start Kafka Streaming"):
    st.sidebar.info("Kafka streaming started. Check messages.")
    while True:
        consumer_message = next(consumer)
        process_message(consumer_message)
        time.sleep(1)
