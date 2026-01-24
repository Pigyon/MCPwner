"""Integration tests for Gosec FastAPI service."""

import requests


class TestGosecService:
    """Test Gosec FastAPI service."""

    def test_health_endpoint(self, docker_compose_up):
        """Test Gosec health endpoint."""
        response = requests.get("http://localhost:8084/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "gosec"

    def test_version_endpoint(self, docker_compose_up):
        """Test Gosec version endpoint."""
        response = requests.get("http://localhost:8084/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["status"] == "success"
