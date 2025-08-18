# Use the official Python runtime as a parent image
FROM python:3.12.7

# Set the working directory inside the container
WORKDIR /kafka/consumer

# Copy the contents of the current directory into the container
COPY . .

# Install required Python packages
RUN pip install confluent-kafka python-dotenv pymongo

# Expose port 12345 to allow communication to/from the container.
EXPOSE 12345

# Run the consumer script when the container starts
CMD ["python", "consumer.py"]
