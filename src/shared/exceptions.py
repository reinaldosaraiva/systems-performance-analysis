"""Custom exceptions for the system performance application."""


class SystemPerformanceError(Exception):
    """Base exception for system performance application."""

    pass


class MetricsCollectionError(SystemPerformanceError):
    """Raised when metrics collection fails."""

    pass


class AnalysisError(SystemPerformanceError):
    """Raised when performance analysis fails."""

    pass


class LLMServiceError(SystemPerformanceError):
    """Raised when LLM service interaction fails."""

    pass


class RepositoryError(SystemPerformanceError):
    """Raised when repository operations fail."""

    pass


class ValidationError(SystemPerformanceError):
    """Raised when input validation fails."""

    pass
