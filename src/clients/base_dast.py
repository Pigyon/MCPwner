"""Base client for DAST services."""

from clients.base import BaseScanClient


class BaseDastClient(BaseScanClient):
    """Base HTTP client for DAST services."""

    report_tool = "get_dast_report"
