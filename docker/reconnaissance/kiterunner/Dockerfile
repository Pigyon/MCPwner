FROM alpine:3.19 AS builder

# Download kiterunner binary from Assetnote GitHub releases
RUN apk add --no-cache curl tar \
    && curl -sL https://github.com/assetnote/kiterunner/releases/download/v1.0.2/kiterunner_1.0.2_linux_amd64.tar.gz \
       -o /tmp/kiterunner.tar.gz \
    && tar -xzf /tmp/kiterunner.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/kr \
    && rm /tmp/kiterunner.tar.gz

FROM alpine:3.19

# Install Python, pip, and curl for healthcheck
RUN apk add --no-cache python3 py3-pip curl \
    && ln -sf python3 /usr/bin/python

# Copy kiterunner binary from builder
COPY --from=builder /usr/local/bin/kr /usr/local/bin/kr

WORKDIR /app

# Copy requirements and install service dependencies
COPY docker/reconnaissance/kiterunner/requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/reconnaissance/kiterunner/main.py .

EXPOSE 8121

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8121"]
