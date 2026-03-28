FROM projectdiscovery/httpx:v1.9.0

# Install Python on top of the official httpx image
RUN apk add --no-cache python3 py3-pip curl

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY docker/reconnaissance/httpx/requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/reconnaissance/httpx/main.py .

# Expose port
EXPOSE 8112

# Reset entrypoint from base image and run the service
ENTRYPOINT []
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8112"]
