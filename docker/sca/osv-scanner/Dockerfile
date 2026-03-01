FROM python:3.11-alpine

# Install osv-scanner from Alpine community repository
RUN apk add --no-cache osv-scanner --repository=http://dl-cdn.alpinelinux.org/alpine/v3.23/community

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY docker/sca/osv-scanner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
