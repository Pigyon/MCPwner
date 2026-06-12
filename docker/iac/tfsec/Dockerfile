# Stage 1: tfsec binary
FROM aquasec/tfsec:v1.28.14 AS tfsec

# Stage 2: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/iac/tfsec/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Lean runtime
FROM python:3.11-alpine

RUN apk add --no-cache gcompat

COPY --from=tfsec /usr/bin/tfsec /usr/local/bin/tfsec
COPY --from=deps /install /usr/local

WORKDIR /service

COPY docker/common /service/common
COPY docker/iac/tfsec/main.py .

EXPOSE 8143

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8143"]
