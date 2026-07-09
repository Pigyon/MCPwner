FROM checkmarx/kics:v2.1.20 AS kics

FROM python:3.11-alpine AS deps

COPY docker/iac/kics/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-alpine

RUN apk add --no-cache gcompat

COPY --from=kics /app/bin/kics /usr/local/bin/kics
COPY --from=kics /app/bin/assets /app/bin/assets
COPY --from=deps /install /usr/local

WORKDIR /service

COPY docker/common /service/common
COPY docker/iac/kics/main.py .

EXPOSE 8141

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8141"]
