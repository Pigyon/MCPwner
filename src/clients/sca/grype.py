
from clients.base import BaseSCAClient

class GrypeClient(BaseSCAClient):
    """Client for Grype service."""
    
    def __init__(self, service_url: str):
        super().__init__(service_url, "grype")
