"""
Centralized logging configuration for Clod_v2
Console-only logging for simplicity
"""

import logging
import sys
from pathlib import Path

# Add project root to path for config import
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance (console only).
    
    Args:
        name: Name of the logger (typically __name__ of the module)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Console handler only
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger
