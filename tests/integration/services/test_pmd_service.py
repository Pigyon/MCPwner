"""Integration tests for PMD FastAPI service."""

import requests


class TestPMDService:
    """Test PMD FastAPI service."""

    def test_health_endpoint(self, docker_compose_up):
        """Test PMD health endpoint."""
        response = requests.get("http://localhost:8086/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pmd"

    def test_version_endpoint(self, docker_compose_up):
        """Test PMD version endpoint."""
        response = requests.get("http://localhost:8086/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["status"] == "success"
