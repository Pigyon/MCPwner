# Pin by digest for byte-for-byte reproducibility (tag v4.8 as of 2026-06-06)
FROM opensecurity/nodejsscan:v4.8@sha256:1f0c0c18f82c1771fba4f9712670d61fd501316eb0fda9d3acf9b6d1a8a30c4d

USER root

# Bullseye predates PEP 668; plain system pip is correct (no venv bootstrap without python3-venv).
COPY docker/sast/nodejsscan/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/nodejsscan/main.py .

EXPOSE 8088

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8088"]
