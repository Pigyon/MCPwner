# Stage 1: Build masscan from source
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git gcc g++ make libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
RUN git clone --depth 1 --branch 1.3.2 https://github.com/robertdavidgraham/masscan.git && \
    cd masscan && make && make install && \
    cd / && rm -rf /tmp/masscan

# Stage 2: Lean runtime
FROM python:3.11-slim

# Only runtime lib needed for masscan
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap0.8 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/bin/masscan /usr/bin/masscan

WORKDIR /app

COPY docker/reconnaissance/masscan/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/common /app/common
COPY docker/reconnaissance/masscan/main.py .

EXPOSE 8117

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8117"]
