"""Integration tests for Brakeman FastAPI service."""

import requests


class TestBrakemanService:
    """Test Brakeman FastAPI service."""

    def test_health_endpoint(self, docker_compose_up):
        """Test Brakeman health endpoint."""
        response = requests.get("http://localhost:8085/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "brakeman"

    def test_version_endpoint(self, docker_compose_up):
        """Test Brakeman version endpoint."""
        response = requests.get("http://localhost:8085/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["status"] == "success"
