FROM trufflesecurity/trufflehog:3.93.6 AS trufflehog

FROM python:3.11-alpine AS deps

COPY docker/secrets/trufflehog/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-alpine

RUN apk add --no-cache curl git

COPY --from=trufflehog /usr/bin/trufflehog /usr/bin/trufflehog
COPY --from=deps /install /usr/local

WORKDIR /service

COPY docker/common /service/common
COPY docker/secrets/trufflehog/main.py .

EXPOSE 8091

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8091"]
