"""Integration tests for Semgrep FastAPI service."""

import requests


class TestSemgrepService:
    """Test Semgrep FastAPI service."""
    
    def test_health_endpoint(self, docker_compose_up):
        """Test Semgrep health endpoint."""
        response = requests.get("http://localhost:8082/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "semgrep"
    
    def test_version_endpoint(self, docker_compose_up):
        """Test Semgrep version endpoint."""
        response = requests.get("http://localhost:8082/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["status"] == "success"
