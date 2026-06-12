# Stage 1: hadolint binary (musl-static, from the alpine variant)
FROM hadolint/hadolint:v2.14.0-alpine AS hadolint

# Stage 2: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/iac/hadolint/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Lean runtime
FROM python:3.11-alpine

COPY --from=hadolint /bin/hadolint /usr/local/bin/hadolint
COPY --from=deps /install /usr/local

WORKDIR /service

COPY docker/common /service/common
COPY docker/iac/hadolint/main.py .

EXPOSE 8144

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8144"]
