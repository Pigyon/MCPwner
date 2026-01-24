"""CSV parsing utilities for CodeQL results."""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Callable

logger = logging.getLogger(__name__)


def parse_csv_results(
    csv_file: str,
    row_parser: Callable[[List[str]], Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Parse CSV file using provided row parser.
    
    Args:
        csv_file: Path to CSV file
        row_parser: Function to parse each row
        
    Returns:
        List of parsed dictionaries
    """
    results = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            
            for row in reader:
                try:
                    parsed = row_parser(row)
                    results.append(parsed)
                except Exception as e:
                    logger.warning(f"Failed to parse row: {row}, error: {e}")
                    continue
    finally:
        # Cleanup CSV file
        Path(csv_file).unlink(missing_ok=True)
    
    return results
