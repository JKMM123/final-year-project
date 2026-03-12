class UsernameOrPhoneNotFoundError(Exception):
    """Exception raised when the username or phone number is not found."""
    def __init__(self, message="Username or phone number not found."):
        self.message = message
        super().__init__(self.message)


class InvalidPasswordError(Exception):
    """Exception raised when the password is invalid."""
    def __init__(self, message="Invalid password."):
        self.message = message
        super().__init__(self.message)


class OTPAlreadyExistsError(Exception):
    """Exception raised when an OTP already exists for the user."""
    def __init__(self, message="An OTP already exists for your number please check your messages."):
        self.message = message
        super().__init__(self.message)


class OTPInvalidError(Exception):
    """Exception raised when the OTP is invalid."""
    def __init__(self, message="Invalid OTP please check your messages."):
        self.message = message
        super().__init__(self.message)

class InvalidResetTokenError(Exception):
    """Exception raised when the password reset token is invalid."""
    def __init__(self, message="Invalid password reset token."):
        self.message = message
        super().__init__(self.message)

class ErrorSendingOTP(Exception):
    def __init__(self, message="Error sending OTP. Please try again later."):
        self.message = message
        super().__init__(self.message)

        
