FROM python:3.11-slim

# Install wafw00f and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir wafw00f==2.4.2

WORKDIR /app

# Copy requirements and install service dependencies
COPY docker/reconnaissance/wafw00f/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/reconnaissance/wafw00f/main.py .

EXPOSE 8120

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8120"]
