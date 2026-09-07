"""
Structured logging configuration using Loguru.
"""

import sys
from loguru import logger

# Remove default logger configuration
logger.remove()

# Add custom styled handler
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

__all__ = ["logger"]
