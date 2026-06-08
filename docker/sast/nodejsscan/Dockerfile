# Pin by digest for byte-for-byte reproducibility (tag v4.8 as of 2026-06-06)
FROM opensecurity/nodejsscan:v4.8@sha256:1f0c0c18f82c1771fba4f9712670d61fd501316eb0fda9d3acf9b6d1a8a30c4d

USER root

# This base is Debian 11 (bullseye, Python 3.9) which predates PEP 668 — it has
# no EXTERNALLY-MANAGED marker and no ensurepip/venv, so a plain pip install into
# the system interpreter is correct here (no --break-system-packages needed, and
# a venv can't be created without python3-venv which the base lacks).
COPY docker/sast/nodejsscan/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/nodejsscan/main.py .

EXPOSE 8088

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8088"]
