# Stage 1: Install Python deps
FROM python:3.11-alpine AS builder

COPY docker/sast/bandit/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Lean runtime
FROM python:3.11-alpine

COPY --from=builder /install /usr/local

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/bandit/main.py .

EXPOSE 8083

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8083"]
