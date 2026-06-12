# Checkov ships as a Python application image. Run the MCPwner HTTP service in an
# isolated virtualenv so its FastAPI/pydantic stack never clashes with Checkov's
# own pinned dependencies; the checkov CLI is invoked as a subprocess.
FROM bridgecrew/checkov:3.3.1

USER root

COPY docker/iac/checkov/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/svc \
    && /opt/svc/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/iac/checkov/main.py .

EXPOSE 8140

# Override Checkov's own entrypoint so CMD runs the service rather than the CLI.
ENTRYPOINT []
CMD ["/opt/svc/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8140"]
