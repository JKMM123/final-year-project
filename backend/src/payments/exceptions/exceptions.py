class PaymentNotFoundError(Exception):
    def __init__(self, message: str = "Payment not found."):
        super().__init__(message)
        self.message = message


class BillNotFoundError(Exception):
    def __init__(self, message: str = "Bill not found."):
        super().__init__(message)
        self.message = message


class MeterNotFoundError(Exception):
    def __init__(self, message: str = "Meter not found."):
        super().__init__(message)
        self.message = message


class BillAlreadyPaidError(Exception):
    def __init__(self, message: str = "Bill is already fully paid."):
        super().__init__(message)
        self.message = message


class InvalidPaymentAmountError(Exception):
    def __init__(self, message: str = "Invalid payment amount."):
        super().__init__(message)
        self.message = message


class PaymentExceedsBillAmountError(Exception):
    def __init__(self, message: str = "Payment amount exceeds remaining bill amount."):
        super().__init__(message)
        self.message = message


class InsufficientPermissionsError(Exception):
    def __init__(self, message: str = "Insufficient permissions to perform this action."):
        super().__init__(message)
        self.message = message