"""Pytest configuration for integration tests."""

import time

import pytest
import requests


@pytest.fixture(scope="session")
def docker_compose_up():
    """Assume docker-compose services are already running."""
    print("\n🐳 Assuming Docker Compose services are running...")
    print("⏳ Waiting for services to be healthy...")
    time.sleep(5)

    # Verify services are up
    services = [
        ("CodeQL", 8080, "/health"),
        ("Linguist", 8081, "/health"),
        ("Semgrep", 8082, "/health"),
    ]

    for service_name, port, endpoint in services:
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"http://localhost:{port}{endpoint}", timeout=2)
                if response.status_code == 200:
                    print(f"✅ {service_name} service is healthy")
                    break
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    raise RuntimeError(f"❌ {service_name} service failed to start")
                time.sleep(1)

    # Check MCP SSE with POST request
    print("⏳ Checking MCP SSE service...")
    max_retries = 30
    for i in range(max_retries):
        try:
            # Send a simple ping request
            response = requests.post(
                "http://localhost:13371/sse",
                json={"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
                timeout=5,
            )
            # Any response means the server is up
            print("✅ MCP SSE service is healthy")
            break
        except requests.exceptions.RequestException:
            if i == max_retries - 1:
                print("⚠️  MCP SSE service not responding, but continuing...")
                break
            time.sleep(1)

    yield

    # Teardown - don't stop services, let them keep running
    print("\n✅ Tests complete (services left running)")
