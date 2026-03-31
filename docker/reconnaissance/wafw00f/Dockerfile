# Stage 1: Install Python deps
FROM python:3.11-alpine AS builder

COPY docker/reconnaissance/wafw00f/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install wafw00f==2.4.2 && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Lean runtime
FROM python:3.11-alpine

RUN apk add --no-cache curl

COPY --from=builder /install /usr/local

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/wafw00f/main.py .

EXPOSE 8120

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8120"]
