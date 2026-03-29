


class RatesException(Exception):
    """Base exception for Rates module."""
    def __init__(self, message: str = "An error occurred in the Rates module."):
        self.message = message
        super().__init__(self.message)


class RateNotFoundError(RatesException):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)




