"""Integration tests for FastAPI services."""

import pytest
import requests

SERVICES = [
    (8080, "codeql", False, None),
    (8081, "linguist", True, "linguist"),
    (8082, "semgrep", True, "standard"),
    (8083, "bandit", True, "standard"),
    (8084, "gosec", True, "standard"),
    (8085, "brakeman", True, "standard"),
    (8086, "pmd", True, "standard"),
    (8087, "psalm", True, "standard"),
]


@pytest.mark.parametrize("port, service_name, has_version, version_check_type", SERVICES)
class TestServices:
    def test_health_endpoint(
        self, docker_compose_up, port, service_name, has_version, version_check_type
    ):
        response = requests.get(f"http://localhost:{port}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        if service_name != "codeql":
            assert data["service"] == service_name

    def test_version_endpoint(
        self, docker_compose_up, port, service_name, has_version, version_check_type
    ):
        if not has_version:
            pytest.skip(f"Service {service_name} does not have a version endpoint")
        response = requests.get(f"http://localhost:{port}/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        if version_check_type == "linguist":
            assert "linguist" in data["version"].lower()
        else:
            assert data["status"] == "success"
