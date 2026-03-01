FROM crazymax/linguist:9.2.0

# Switch to root for installation
USER root

# Install Python and FastAPI/uvicorn for the HTTP service
COPY docker/linguist/requirements.txt /tmp/requirements.txt
RUN apk add --no-cache python3 py3-pip curl && \
    pip3 install --break-system-packages --no-cache-dir -r /tmp/requirements.txt

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
