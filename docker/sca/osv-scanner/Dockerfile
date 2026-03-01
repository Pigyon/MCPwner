FROM python:3.11-alpine

# Install osv-scanner from Alpine community repository
RUN apk add --no-cache osv-scanner --repository=http://dl-cdn.alpinelinux.org/alpine/v3.23/community

# Create app directory
WORKDIR /app

# Install Python dependencies with pinned versions
RUN pip install --no-cache-dir fastapi==0.115.12 uvicorn==0.34.0

# Copy application code
COPY docker/common /app/common
COPY docker/sca/osv-scanner/main.py /app/main.py

# Create non-root user
RUN adduser -D scanner
USER scanner

# Expose port
EXPOSE 8100

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]
