"""Base client for Reconnaissance services."""

from clients.base import BaseScanClient


class BaseReconnaissanceClient(BaseScanClient):
    """Base HTTP client for Reconnaissance services."""

    report_tool = "get_reconnaissance_report"
