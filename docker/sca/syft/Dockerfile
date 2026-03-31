# Stage 1: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/sca/syft/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Lean runtime
FROM python:3.11-alpine

COPY --from=anchore/syft:v1.42.1-nonroot /syft /usr/local/bin/syft

RUN apk add --no-cache gcompat

COPY --from=deps /install /usr/local

WORKDIR /app

COPY docker/common /app/common
COPY docker/sca/syft/main.py /app/main.py

ENV XDG_CACHE_HOME=/app/cache
RUN mkdir -p /app/cache/syft && \
    adduser -D scanner && chown -R scanner:scanner /app/cache

USER scanner

EXPOSE 8102

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8102"]
