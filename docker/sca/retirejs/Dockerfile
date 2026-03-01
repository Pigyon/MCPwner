FROM python:3.11-alpine

# Install Node.js and NPM (for Retire.js)
RUN apk add --no-cache nodejs npm

# Install Retire.js globally
RUN npm install -g retire@5.4.2

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY docker/sca/retirejs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY docker/common /app/common
COPY docker/sca/retirejs/main.py /app/main.py

# Create non-root user
RUN adduser -D scanner
USER scanner

# Expose port
EXPOSE 8104

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8104"]
