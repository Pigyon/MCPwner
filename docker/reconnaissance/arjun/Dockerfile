FROM python:3.11-slim

# Install arjun and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir arjun==2.2.7

WORKDIR /app

# Copy requirements and install service dependencies
COPY docker/reconnaissance/arjun/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/reconnaissance/arjun/main.py .

EXPOSE 8119

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8119"]
