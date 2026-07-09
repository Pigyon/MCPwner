FROM python:3.12-alpine AS deps

COPY docker/reconnaissance/nmap/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM instrumentisto/nmap:7

USER root

RUN apk add --no-cache python3
COPY --from=deps /install /usr

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/nmap/main.py .

EXPOSE 8116

ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8116"]
