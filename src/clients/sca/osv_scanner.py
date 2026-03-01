from clients.base import BaseSCAClient


class OSVScannerClient(BaseSCAClient):
    """Client for OSV-Scanner service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "osv-scanner")
