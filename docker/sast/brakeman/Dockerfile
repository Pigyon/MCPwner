FROM ruby:3.2-slim

# Install Brakeman
RUN gem install brakeman

# Install Python and pip for FastAPI service
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY docker/sast/brakeman/requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/sast/brakeman/main.py .

# Expose service port
EXPOSE 8085

# Run the FastAPI service with uvicorn
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8085"]
