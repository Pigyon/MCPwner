# Stage 1: Install Python deps
FROM python:3.12-alpine AS builder

COPY docker/utilities/fuzzer/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Lean runtime
FROM python:3.12-alpine

COPY --from=builder /install /usr/local

WORKDIR /service

COPY docker/utilities/fuzzer/main.py .

EXPOSE 8132

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8132"]
