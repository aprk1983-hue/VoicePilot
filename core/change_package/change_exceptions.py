"""Exceptions for the Engineering Change Package engine."""


class ChangePackageError(Exception):
    """Base error for change package generation."""


class ChangePackageCaseError(ChangePackageError):
    """Raised when a case cannot produce a change package."""

    def __init__(self, case_id: str, message: str) -> None:
        super().__init__(message)
        self.case_id = case_id
