# Stage 1: Install Python deps
FROM python:3.11-alpine AS builder

COPY docker/reconnaissance/arjun/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install arjun==2.2.7 && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Lean runtime
FROM python:3.11-alpine

RUN apk add --no-cache curl

COPY --from=builder /install /usr/local

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/arjun/main.py .

EXPOSE 8119

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8119"]
