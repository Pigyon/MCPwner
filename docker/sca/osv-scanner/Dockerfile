# Stage 1: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/sca/osv-scanner/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Lean runtime
FROM python:3.11-alpine

RUN apk add --no-cache osv-scanner --repository=http://dl-cdn.alpinelinux.org/alpine/v3.23/community

COPY --from=deps /install /usr/local

WORKDIR /app

COPY docker/common /app/common
COPY docker/sca/osv-scanner/main.py /app/main.py

RUN adduser -D scanner
USER scanner

EXPOSE 8100

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]
