# Stage 1: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/sca/retirejs/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Install retire.js
FROM node:22-alpine AS node-deps

RUN npm install -g retire@5.4.2

# Stage 3: Lean runtime
FROM python:3.11-alpine

RUN apk add --no-cache nodejs

# Copy retire.js from node stage
COPY --from=node-deps /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node-deps /usr/local/bin/retire /usr/local/bin/retire

COPY --from=deps /install /usr/local

WORKDIR /app

COPY docker/common /app/common
COPY docker/sca/retirejs/main.py /app/main.py

RUN adduser -D scanner
USER scanner

EXPOSE 8104

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8104"]
