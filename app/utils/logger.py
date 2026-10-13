"""Telemetry logger using Loguru for tracking validation failures and runtime metrics."""

import os
import sys
from typing import Any, List
from loguru import logger
from app.schemas.request import ValidationErrorDetail

# Ensure logs directory exists
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
FAILURE_LOG_PATH = os.path.join(LOG_DIR, "validation_failures.log")

# Configure Loguru
logger.remove()

# 1. Console Output (Clean, human-readable)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)

# 2. File Output (Structured telemetry for validation diagnostics)
logger.add(
    FAILURE_LOG_PATH,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="WARNING",
    rotation="10 MB",
    retention="14 days",
    compression="zip",
)


def log_validation_failure(
    attempt: int,
    errors: List[ValidationErrorDetail],
    raw_snippet: str,
) -> None:
    """Log a structured summary when an LLM response fails Pydantic schema validation.

    Args:
        attempt: The retry attempt index (1-based).
        errors: List of structured ValidationErrorDetail instances.
        raw_snippet: A truncated preview of the LLM's invalid response.
    """
    error_summary = "; ".join(f"[{err.field}: {err.message}]" for err in errors)
    preview = (raw_snippet[:150] + "...") if len(raw_snippet) > 150 else raw_snippet

    logger.warning(
        f"[VALIDATION FAILED] Attempt {attempt} | Errors: {error_summary} | Raw Response Preview: '{preview}'"
    )
