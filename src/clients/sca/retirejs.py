from clients.base import BaseSCAClient


class RetireJSClient(BaseSCAClient):
    """Client for Retire.js service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "retirejs")
