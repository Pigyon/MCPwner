FROM instrumentisto/nmap:7

# Switch to root to install packages
USER root

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY docker/enumeration_discovery/nmap/requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/enumeration_discovery/nmap/main.py .

# Expose port
EXPOSE 8116

# Reset entrypoint from base image and run the service
ENTRYPOINT []
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8116"]
