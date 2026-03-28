FROM blacklanternsecurity/bbot:2.8-full

# Install FastAPI service dependencies
WORKDIR /app
COPY docker/reconnaissance/bbot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/reconnaissance/bbot/main.py .

# Pre-install all module dependencies so scans don't stall
RUN bbot --install-all-deps || true

EXPOSE 8118

# Override the bbot entrypoint so we can run uvicorn
ENTRYPOINT []
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8118"]
