FROM ipvsix/opengrep:1.16.4

# Install Python and pip for FastAPI wrapper (Alpine-based image)
RUN apk add --no-cache python3 py3-pip curl

# Install FastAPI wrapper dependencies
COPY docker/sast/opengrep/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/opengrep/main.py .

EXPOSE 8096

# Override the base image's entrypoint (opengrep scan) so we can run our FastAPI wrapper
ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8096"]
