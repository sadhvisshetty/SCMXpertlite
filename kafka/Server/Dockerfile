# Use the official Python runtime as a parent image
FROM python:3.12.7

# Set the working directory inside the container
WORKDIR /kafka/server

# Copy the contents of the current directory into the container
COPY . .

# Install required Python packages
RUN pip install confluent-kafka

# Expose port 12345 to allow communication (since your server listens on this port)
EXPOSE 12345

# Run the server script when the container starts
CMD ["python", "server.py"]
