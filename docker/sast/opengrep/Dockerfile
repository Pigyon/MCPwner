# Stage 1: Install Python deps in builder to avoid pip cache in final image
FROM python:3.11-alpine AS deps

COPY docker/sast/opengrep/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime on vendor image
FROM ipvsix/opengrep:1.16.4

RUN apk add --no-cache python3 curl

# Copy pre-built Python packages
COPY --from=deps /install /usr

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/opengrep/main.py .

EXPOSE 8096

ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8096"]
