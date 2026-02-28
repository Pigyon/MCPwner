FROM securego/gosec:latest

# Switch to root for installation
USER root

# Install Python and pip for FastAPI
RUN apk add --no-cache python3 py3-pip

# Install FastAPI and uvicorn for the HTTP service
RUN pip3 install --break-system-packages --no-cache-dir fastapi uvicorn

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/gosec/main.py .

# Expose service port
EXPOSE 8084

# Override the entrypoint to run our FastAPI service
ENTRYPOINT []

# Run the FastAPI service with uvicorn
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084"]
