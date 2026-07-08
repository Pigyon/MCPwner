FROM python:3.11-slim AS deps

COPY docker/dast/jwt_tool/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG JWT_TOOL_VERSION=2.3.0
RUN curl -fsSL "https://github.com/ticarpi/jwt_tool/archive/refs/tags/v${JWT_TOOL_VERSION}.tar.gz" \
    | tar -xz -C /opt \
    && mv "/opt/jwt_tool-${JWT_TOOL_VERSION}" /opt/jwt_tool \
    && pip install --no-cache-dir -r /opt/jwt_tool/requirements.txt

COPY --from=deps /install /usr/local
WORKDIR /app
COPY docker/common /app/common
COPY docker/dast/jwt_tool/main.py .

EXPOSE 8166
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8166"]
