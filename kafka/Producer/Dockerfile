# Use the official Python runtime as a parent image
FROM python:3.12.7

# Set the working directory inside the container
WORKDIR /kafka/producer

# Copy the contents of the current directory into the container
COPY . .

# Install required Python packages
RUN pip install confluent-kafka python-dotenv

# Expose port 12345 (only if your producer actually listens on this port; otherwise, you can remove this)
EXPOSE 12345

# Run the producer script when the container starts
CMD ["python", "producer.py"]
