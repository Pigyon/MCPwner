"""Pytest configuration for integration tests."""

import time

import pytest
import requests

from tests.integration.services.test_services import SERVICES


@pytest.fixture(scope="session")
def docker_compose_up():
    """Assume docker-compose services are already running."""
    print("\n🐳 Assuming Docker Compose services are running...")
    print("⏳ Waiting for services to be healthy...")
    time.sleep(5)

    # Extract just the port and service name from the SERVICES config
    services_to_check = [
        (service_name.capitalize(), port, "/health") for port, service_name, _, _ in SERVICES
    ]

    for service_name, port, endpoint in services_to_check:
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

    yield

    # Teardown - don't stop services, let them keep running
    print("\n✅ Tests complete (services left running)")
