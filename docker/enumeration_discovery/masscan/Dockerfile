FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    make \
    libpcap-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Build Masscan from source (version 1.3.2)
WORKDIR /tmp
RUN git clone https://github.com/robertdavidgraham/masscan.git && \
    cd masscan && \
    git checkout 1.3.2 && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/masscan

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY docker/enumeration_discovery/masscan/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/enumeration_discovery/masscan/main.py .

# Expose port
EXPOSE 8117

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8117"]
