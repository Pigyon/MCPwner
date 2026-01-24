"""Integration tests for CodeQL FastAPI service."""

import requests


class TestCodeQLService:
    """Test CodeQL FastAPI service."""
    
    def test_health_endpoint(self, docker_compose_up):
        """Test CodeQL health endpoint."""
        response = requests.get("http://localhost:8080/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
