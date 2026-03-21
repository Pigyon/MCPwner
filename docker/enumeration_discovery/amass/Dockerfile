FROM golang:1.24-alpine AS builder

# Install Amass v5.0.1
RUN apk add --no-cache git && \
    go install -v github.com/owasp-amass/amass/v5/...@v5.0.1

FROM alpine:latest

# Install Python, curl, and runtime dependencies
RUN apk add --no-cache python3 py3-pip ca-certificates curl

# Copy Amass binary from builder
COPY --from=builder /go/bin/amass /usr/local/bin/amass

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY docker/enumeration_discovery/amass/requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/enumeration_discovery/amass/main.py .

# Expose port
EXPOSE 8111

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8111"]
