class AppError(Exception):
    """Base exception for the application."""


class InvalidNameError(AppError):
    """Raised when the input name is invalid."""