# Stage 1: Install Python deps
FROM python:3.11-alpine AS builder

COPY docker/secrets/whispers/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Lean runtime
FROM python:3.11-alpine

RUN apk add --no-cache git

COPY --from=builder /install /usr/local

WORKDIR /service

COPY docker/common /service/common
COPY docker/secrets/whispers/main.py .

EXPOSE 8092

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8092"]
