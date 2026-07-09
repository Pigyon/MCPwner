# Atheris 1.0.3 needs Python 3.9; pip builds against libclang_rt.fuzzer_no_main via $LIBFUZZER_LIB.
FROM python:3.9-slim

# clang + libclang-rt-dev + g++ provide libFuzzer archive, C++ headers, and linker.
RUN apt-get update && apt-get install -y --no-install-recommends \
        clang \
        libclang-rt-dev \
        g++ \
    && rm -rf /var/lib/apt/lists/*

ENV CC=clang \
    CXX=clang++ \
    CLANG_BIN=/usr/bin/clang

COPY docker/fuzzing/atheris/requirements.txt /tmp/requirements.txt
RUN set -eu; \
    LIBFUZZER_LIB="$(find /usr/lib -name 'libclang_rt.fuzzer_no_main-x86_64.a' | head -1)"; \
    test -n "$LIBFUZZER_LIB"; \
    export LIBFUZZER_LIB; \
    echo "Building atheris against $LIBFUZZER_LIB"; \
    pip install --no-cache-dir -r /tmp/requirements.txt; \
    rm -f /tmp/requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/fuzzing/atheris/main.py .

EXPOSE 8150

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8150"]
