FROM python:3.11-alpine

# Install Grype via official installer or apk
# Alpine community repo often has grype, but we should use the version matching our goal if possible
# or copy from official image.
# Using official image as source is safer for version pinning.

COPY --from=anchore/grype:v0.109.0-nonroot /grype /usr/local/bin/grype

# Create app directory
WORKDIR /app

# Install Python dependencies with pinned versions
RUN apk add --no-cache gcompat && \
    pip install --no-cache-dir fastapi==0.115.12 uvicorn==0.34.0

# Copy application code
COPY docker/common /app/common
COPY docker/sca/grype/main.py /app/main.py

# Grype needs a cache directory for DB
# By default it uses $XDG_CACHE_HOME/grype or ~/.cache/grype
# We need to ensure this directory is writable by 'scanner' user
ENV XDG_CACHE_HOME=/app/cache
RUN mkdir -p /app/cache/grype

# Create non-root user
RUN adduser -D scanner && chown -R scanner:scanner /app/cache
USER scanner

# Expose port
EXPOSE 8101

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8101"]
