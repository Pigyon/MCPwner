# Stage 1: Install Python deps
FROM python:3.11-slim AS deps

COPY docker/dast/nosqlmap/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime — NoSQLMap requires Python 2 which is EOL and unavailable
# on modern Debian. Instead we clone the repo for reference payloads and drive
# the injection logic from the Python 3 wrapper.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG NOSQLMAP_COMMIT=5a6dc7a0477345a424bc66f76cb7a2634c61a3af
RUN git clone https://github.com/codingo/NoSQLMap.git /opt/nosqlmap \
    && cd /opt/nosqlmap \
    && git checkout "${NOSQLMAP_COMMIT}"

COPY --from=deps /install /usr/local
WORKDIR /app

COPY docker/common /app/common
COPY docker/dast/nosqlmap/main.py .

EXPOSE 8161
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8161"]
