from confluent_kafka import Consumer
import json, os
from pymongo import MongoClient
from pymongo.database import Database


connection_string = os.getenv("MONGODB_URI")
database_name = os.getenv("MONGODB_DATABASE")

if not connection_string or not database_name:
    raise ValueError("MongoDB connection string or database name is not set in .env")

client = MongoClient(connection_string)
database = client[database_name]
device_data_stream1 = database["devices"]

bootstrap_servers = os.getenv("BOOTSTRAP_SERVERS")
if not bootstrap_servers:
    raise ValueError("Kafka bootstrap servers are not set in .env")

consumer_config = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'my-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(consumer_config)
consumer.subscribe(['device_data_stream'])

try:
    while True:
        msg = consumer.poll(1.0)  # Polls Kafka for messages. The argument 1.0 is the timeout in seconds.
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        try:
            raw_message = msg.value().decode('utf-8')
            print(f"Raw message received: {raw_message}")
            data = json.loads(raw_message)

            if isinstance(data, str):
                data = json.loads(data)

            print(f"Deserialized data: {data}")

            if isinstance(data, list):
                result = device_data_stream1.insert_many(data)
                print(f"Inserted {len(result.inserted_ids)} documents into MongoDB")
            elif isinstance(data, dict):
                result = device_data_stream1.insert_one(data)
                print(f"Inserted 1 document into MongoDB with id: {result.inserted_id}")
            else:
                print(f"Invalid data format: {data}")
        except Exception as e:
            print(f"Error processing message: {str(e)}")

except KeyboardInterrupt:
    print("Consumer interrupted by user.")

finally:
    consumer.close()
