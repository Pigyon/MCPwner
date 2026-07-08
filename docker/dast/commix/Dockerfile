FROM python:3.11-slim AS deps

COPY docker/dast/commix/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG COMMIX_VERSION=4.1
RUN curl -fsSL "https://github.com/commixproject/commix/archive/refs/tags/v${COMMIX_VERSION}.tar.gz" \
    | tar -xz -C /opt \
    && mv "/opt/commix-${COMMIX_VERSION}" /opt/commix

COPY --from=deps /install /usr/local
WORKDIR /app
COPY docker/common /app/common
COPY docker/dast/commix/main.py .

EXPOSE 8162
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8162"]
