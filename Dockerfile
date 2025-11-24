# Use Python 3.11 as base image (compatible with 3.9-3.12 requirement)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unzip \
    wget \
    curl \
    # Dependencies for Selenium/Chrome
    chromium \
    chromium-driver \
    # Additional dependencies for headless browser
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY rede/requirements.txt /app/requirements.txt
COPY rede_cria_tabelas/requirements.txt /app/rede_cria_tabelas_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r rede_cria_tabelas_requirements.txt

# Copy the application code
COPY rede/ /app/
COPY rede_cria_tabelas/ /app/rede_cria_tabelas/

# Create necessary directories and symlinks
RUN mkdir -p /app/bases /app/arquivos /app/static /app/templates && \
    ln -s /usr/bin/chromium /usr/bin/google-chrome || true

# Expose the Flask port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=rede.py
# Chrome/Chromium environment variables for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_BIN=/usr/bin/chromium
ENV DISPLAY=:99

# Run the application
CMD ["python", "rede.py"]

