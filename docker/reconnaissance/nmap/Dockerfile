# Stage 1: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/reconnaissance/nmap/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime on vendor image
FROM instrumentisto/nmap:7

USER root

RUN apk add --no-cache python3
COPY --from=deps /install /usr

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/nmap/main.py .

EXPOSE 8116

ENTRYPOINT []
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8116"]
