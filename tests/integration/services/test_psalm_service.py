"""Integration tests for Psalm FastAPI service."""

import requests


class TestPsalmService:
    """Test Psalm FastAPI service."""

    def test_health_endpoint(self, docker_compose_up):
        """Test Psalm health endpoint."""
        response = requests.get("http://localhost:8087/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "psalm"

    def test_version_endpoint(self, docker_compose_up):
        """Test Psalm version endpoint."""
        response = requests.get("http://localhost:8087/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["status"] == "success"
