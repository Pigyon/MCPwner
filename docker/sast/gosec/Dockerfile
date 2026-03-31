# Stage 1: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/sast/gosec/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime on vendor image
FROM securego/gosec:2.24.6

USER root

# Copy pre-built Python packages (avoids pip install in final image)
RUN apk add --no-cache python3
COPY --from=deps /install /usr

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/gosec/main.py .

EXPOSE 8084

ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084"]
