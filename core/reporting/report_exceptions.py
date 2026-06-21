"""Exceptions for the Enterprise Reporting Engine."""


class ReportingError(Exception):
    """Base error for enterprise report generation."""


class UnsupportedReportTypeError(ReportingError):
    """Raised when an unsupported report type is requested."""

    def __init__(self, report_type: str) -> None:
        super().__init__(f"Unsupported report type: {report_type}")
        self.report_type = report_type
