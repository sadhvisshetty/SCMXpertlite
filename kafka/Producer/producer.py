from confluent_kafka import Producer
import json, os, socket

 
bootstrap_servers = os.getenv("BOOTSTRAP_SERVERS")
Host = os.getenv("HOST")
Port = int(os.getenv("PORT"))


try:
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((Host, Port)) 
    server.settimeout(10)
    
 
    
    producer = Producer({"bootstrap.servers": 'kafka:9092'})
 
    
    def send_message(topic, message):
        try:
            producer.produce(topic, value=json.dumps(message))
            producer.flush()
            print(f"Message sent to Kafka topic {topic}: {message}")
        except Exception as kafka_error:
            print(f"Error sending message to Kafka: {kafka_error}")
 
    while True:
        try:
            message = server.recv(1024).decode('utf-8')
            if message:
                print(f"Received message from server: {message}")
                parsed_message = json.loads(message)
                send_message("device_data_stream", parsed_message)
            else:
                print("Received empty message from server")
       
        except socket.timeout:
            print("No messages received in the last 10 seconds.")
       
        except ConnectionResetError:
            print("Connection reset by peer.")
            break
       
        except Exception as general_error:
            print(f"Unexpected error: {general_error}")
            break
 
except socket.error as socket_error:
    print(f"Socket error: {socket_error}")
 
except Exception as general_error:
     print(f"Unexpected error: {general_error}")
 
finally:
    server.close()
