FROM python:3.12-slim

# bash is needed for the "bash" interpreter option; git/curl are common in PoC scripts.
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY docker/poc/sandbox/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/poc/sandbox/main.py .

EXPOSE 8134

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8134"]
