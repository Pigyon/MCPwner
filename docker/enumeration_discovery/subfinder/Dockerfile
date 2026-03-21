FROM projectdiscovery/subfinder:v2.13.0

# Install Python on top of the official subfinder image
RUN apk add --no-cache python3 py3-pip

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY docker/enumeration_discovery/subfinder/requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/enumeration_discovery/subfinder/main.py .

# Expose port
EXPOSE 8110

# Reset entrypoint from base image and run the service
ENTRYPOINT []
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8110"]
