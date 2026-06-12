"""Base HTTP client for Utilities services."""

from clients.base import BaseScanClient


class BaseUtilitiesClient(BaseScanClient):
    """Base HTTP client for Utilities services."""

    report_tool = "get_utilities_report"
