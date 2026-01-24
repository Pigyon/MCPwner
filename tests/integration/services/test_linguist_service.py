"""Integration tests for Linguist FastAPI service."""

import requests


class TestLinguistService:
    """Test Linguist FastAPI service."""
    
    def test_health_endpoint(self, docker_compose_up):
        """Test Linguist health endpoint."""
        response = requests.get("http://localhost:8081/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "linguist"
    
    def test_version_endpoint(self, docker_compose_up):
        """Test Linguist version endpoint."""
        response = requests.get("http://localhost:8081/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "linguist" in data["version"].lower()
