#!/bin/sh
set -eu

POLICY_DIR="${HOME}/.terrascan/pkg/policies/opa/rego"
TERRASCAN_VERSION="${TERRASCAN_VERSION:-1.19.9}"

if [ ! -d "$POLICY_DIR" ]; then
    echo "Terrascan policies not found; fetching v${TERRASCAN_VERSION} from GitHub..."
    for attempt in 1 2 3 4 5; do
        if curl -fsSL \
            "https://github.com/tenable/terrascan/archive/refs/tags/v${TERRASCAN_VERSION}.tar.gz" \
            | tar -xz -C "${HOME}"; then
            mv "${HOME}/terrascan-${TERRASCAN_VERSION}" "${HOME}/.terrascan"
            break
        fi
        echo "Policy download failed (attempt ${attempt}/5); retrying in 10s..."
        sleep 10
    done
    if [ ! -d "$POLICY_DIR" ]; then
        echo "Failed to fetch Terrascan policies" >&2
        exit 1
    fi
fi

exec python -m uvicorn main:app --host 0.0.0.0 --port 8142
