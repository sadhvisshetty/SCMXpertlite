# Use official Python runtime as a base image
FROM python:3.12.7

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker cache
COPY app/backend ./app/backend
COPY app/frontend ./app/frontend
# Install dependencies

RUN pip install --no-cache-dir -r app/backend/requirements.txt


# Expose the port FastAPI runs on (default 8000)
EXPOSE 8000

# Command to run FastAPI using Uvicorn
CMD ["uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]


