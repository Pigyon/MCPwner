FROM python:3.11-alpine

# Use official Syft image as source for binary
COPY --from=anchore/syft:v1.42.1-nonroot /syft /usr/local/bin/syft

# Create app directory
WORKDIR /app

# Install Python dependencies with pinned versions
RUN apk add --no-cache gcompat && \
    pip install --no-cache-dir fastapi==0.115.12 uvicorn==0.34.0

# Copy application code
COPY docker/common /app/common
COPY docker/sca/syft/main.py /app/main.py

# Syft might need cache too
ENV XDG_CACHE_HOME=/app/cache
RUN mkdir -p /app/cache/syft

# Create non-root user
RUN adduser -D scanner && chown -R scanner:scanner /app/cache
USER scanner

# Expose port
EXPOSE 8102

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8102"]
