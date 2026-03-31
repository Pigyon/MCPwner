# Stage 1: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/sast/pmd/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime on vendor image
FROM pmdcode/pmd:7.22.0

USER root

RUN apk add --no-cache python3
COPY --from=deps /install /usr

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/pmd/main.py .

EXPOSE 8086

ENTRYPOINT ["/usr/bin/python3"]
CMD ["-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8086"]
