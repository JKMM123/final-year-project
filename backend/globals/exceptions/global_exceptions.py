from typing import Any


class InternalServerError(Exception):
    """Error logging in exception."""

    def __init__(self, message: str = "Error"):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """Validation error exception."""

    def __init__(self, errors: Any, message: str = "Validation error."):
        self.errors = errors
        self.message = message
        super().__init__(self.message)


class BadRequestError(Exception):
    """Bad request error exception."""

    def __init__(self, error: str, message: str = "Bad request."):
        self.error = error
        self.message = message
        super().__init__(self.message)


class TimeOutException(Exception):
    """Exception raised when a request times out."""

    def __init__(self, message: str = "Request timed out."):
        self.message = message
        super().__init__(self.message)


class UnauthorizedError(Exception):
    """Exception raised for unauthorized access."""

    def __init__(self, message: str = "Unauthorized. "):
        self.message = message
        super().__init__(self.message)


class ForbiddenError(Exception):
    """Exception raised for forbidden access."""

    def __init__(self, message: str = "Forbidden."):
        self.message = message
        super().__init__(self.message)


class TooManyRequestsError(Exception):
    """Exception raised when too many requests are made."""

    def __init__(self, message: str = "Too many requests. Please try again later."):
        self.message = message
        super().__init__(self.message)
