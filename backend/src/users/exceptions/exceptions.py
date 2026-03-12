

class UserNotFoundError(Exception):
    def __init__(self, message: str = "User not found."):
        super().__init__(message)
        self.message = message


class UsernameAlreadyExistsError(Exception):
    def __init__(self, message: str = "Username already exists."):
        super().__init__(message)
        self.message = message


class PhoneNumberAlreadyExistsError(Exception):
    def __init__(self, message: str = "Phone number already exists."):
        super().__init__(message)
        self.message = message


class InsufficientPermissionsException(Exception):
    """Exception raised when a user does not have sufficient permissions to perform an action."""
    def __init__(self, message:str):
        self.message = message
        super().__init__(message)



