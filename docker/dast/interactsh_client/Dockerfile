# Stage 1: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/dast/interactsh_client/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime on vendor image
FROM projectdiscovery/interactsh-client:v1.3.1

RUN apk add --no-cache python3 curl
COPY --from=deps /install /usr

WORKDIR /app

COPY docker/common /app/common
COPY docker/dast/interactsh_client/main.py .

EXPOSE 8167

ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8167"]
