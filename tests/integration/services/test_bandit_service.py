"""Integration tests for Bandit FastAPI service."""

import requests


class TestBanditService:
    """Test Bandit FastAPI service."""

    def test_health_endpoint(self, docker_compose_up):
        """Test Bandit health endpoint."""
        response = requests.get("http://localhost:8083/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bandit"

    def test_version_endpoint(self, docker_compose_up):
        """Test Bandit version endpoint."""
        response = requests.get("http://localhost:8083/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["status"] == "success"
