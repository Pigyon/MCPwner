# Stage 1: Get gitleaks binary
FROM zricethezav/gitleaks:v8.30.0 AS gitleaks

# Stage 2: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/secrets/gitleaks/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Lean runtime
FROM python:3.11-alpine

RUN apk add --no-cache curl git

COPY --from=gitleaks /usr/bin/gitleaks /usr/bin/gitleaks
COPY --from=deps /install /usr/local

WORKDIR /service

COPY docker/common /service/common
COPY docker/secrets/gitleaks/main.py .

EXPOSE 8090

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
