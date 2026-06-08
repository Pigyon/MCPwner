# Stage 1: Install brakeman gem
FROM ruby:3.2-slim AS builder

# build-essential is needed to compile the prism gem's native extension.
# Brakeman 7+ defaults to the Prism parser and aborts if the gem is absent
# ("Asked to use Prism, but failed to load"); Ruby 3.2 doesn't bundle it.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    gem install brakeman prism --no-document && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: Slim runtime
FROM ruby:3.2-slim

# Copy full gem environment from builder (gems + binstubs)
COPY --from=builder /usr/local/bundle /usr/local/bundle

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Install the Python deps into an isolated virtualenv instead of
# --break-system-packages (PEP 668). A venv is self-contained on its own
# sys.path, which also avoids Debian's site-packages/dist-packages split that
# breaks the bare --prefix=/install copy pattern on system-python bases.
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY docker/sast/brakeman/requirements.txt .
RUN python3 -m venv "$VIRTUAL_ENV" && \
    pip install --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/brakeman/main.py .

EXPOSE 8085

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8085"]
