from clients.base import BaseSCAClient


class SyftClient(BaseSCAClient):
    """Client for Syft service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "syft")
