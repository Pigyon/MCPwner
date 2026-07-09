FROM blacklanternsecurity/bbot:2.8-full

WORKDIR /app
COPY docker/reconnaissance/bbot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/common /app/common

COPY docker/reconnaissance/bbot/main.py .

# Pre-install bbot module deps at build time so scans do not stall on first run.
RUN bbot --install-all-deps

EXPOSE 8118

ENTRYPOINT []
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8118"]
