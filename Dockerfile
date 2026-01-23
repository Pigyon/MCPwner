FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash mcpwner

WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p /var/log/mcpwner && \
    chown -R mcpwner:mcpwner /var/log/mcpwner /app

# Switch to non-root user
USER mcpwner

CMD ["python", "server.py"]