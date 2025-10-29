"""Severity value object for performance insights."""

from enum import Enum


class Severity(Enum):
    """Severity levels for performance insights."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
