import logging
import sys
from pathlib import Path
from typing import Any, Dict


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Configure logging based on configuration settings.

    Args:
        config: Configuration dictionary containing a 'logging' section
    """
    logging_config = config.get("logging", {})
    log_level_str = logging_config.get("level", "INFO").upper()
    log_file = logging_config.get("file")

    log_level = getattr(logging, log_level_str, logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    root_logger.handlers = []

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)

    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(f"Failed to setup file logging: {e}\n")

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("docker").setLevel(logging.WARNING)
