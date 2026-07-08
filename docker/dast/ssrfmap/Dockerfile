FROM python:3.11-slim AS deps

COPY docker/dast/ssrfmap/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG SSRFMAP_COMMIT=69103b27f5898d9707630dc572798df63727b90f
RUN git clone https://github.com/swisskyrepo/SSRFmap.git /opt/ssrfmap \
    && cd /opt/ssrfmap \
    && git checkout "${SSRFMAP_COMMIT}" \
    && pip install --no-cache-dir -r requirements.txt

COPY --from=deps /install /usr/local
WORKDIR /app
COPY docker/common /app/common
COPY docker/dast/ssrfmap/main.py .

EXPOSE 8165
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8165"]
