# Use Python 3.11 as base image (compatible with 3.9-3.12 requirement)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY rede/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY rede/ /app/

# Create necessary directories
RUN mkdir -p /app/bases /app/arquivos /app/static /app/templates

# Expose the Flask port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=rede.py

# Run the application
CMD ["python", "rede.py"]

