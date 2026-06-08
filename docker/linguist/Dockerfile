FROM python:3.12-alpine AS deps

COPY docker/linguist/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /tmp/requirements.txt

# Stage 2: Runtime
FROM crazymax/linguist:9.2.0

# Switch to root for installation
USER root

# Bring in the pre-built Python deps. On Alpine, site-packages under /usr IS on
# the default sys.path, so copying the prefix here works without
# --break-system-packages and without a venv (Alpine strips ensurepip, so
# `python3 -m venv` cannot bootstrap pip).
RUN apk add --no-cache python3 curl
COPY --from=deps /install /usr

WORKDIR /service

# Copy service files
COPY docker/linguist/main.py .
COPY src/utils/git_utils.py .

# Expose service port
EXPOSE 8081

# Override the base image's entrypoint
ENTRYPOINT []

# Run the FastAPI service with uvicorn
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
