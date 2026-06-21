"""Exceptions for the Investigation Comparison Engine."""


class ComparisonError(Exception):
    """Base error for investigation comparison."""


class ComparisonSnapshotError(ComparisonError):
    """Raised when snapshot comparison inputs are invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
