FROM python:3.11-slim

WORKDIR /service

# Copy requirements and install dependencies
COPY docker/sast/bandit/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files
COPY docker/common /service/common
COPY docker/sast/bandit/main.py .

# Expose service port
EXPOSE 8083

# Run the FastAPI service with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8083"]
