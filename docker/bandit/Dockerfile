FROM python:3.11-slim

# Install Bandit
RUN pip install --no-cache-dir bandit[sarif]

# Install FastAPI and uvicorn for the HTTP service
RUN pip install --no-cache-dir fastapi uvicorn

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/bandit/main.py .

# Expose service port
EXPOSE 8083

# Run the FastAPI service with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8083"]
