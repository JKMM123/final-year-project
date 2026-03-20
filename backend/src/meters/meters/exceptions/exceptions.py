class MeterNotFoundError(Exception):
    def __init__(self):
        self.message = f"Meter not found."
        super().__init__(self.message)


class CustomerNameAlreadyExistsError(Exception):
    def __init__(self, customer_full_name: str):
        self.customer_full_name = customer_full_name
        self.message = f"Customer with name '{customer_full_name}' already exists in the specified area and address."
        super().__init__(self.message)


class CustomerPhoneNumberAlreadyExistsError(Exception):
    def __init__(self, customer_phone_number: str):
        self.customer_phone_number = customer_phone_number
        self.message = f"Customer with phone number '{customer_phone_number}' already exists."
        super().__init__(self.message)


class CustomerIdentityAddressAlreadyExistsError(Exception):
    def __init__(self, customer_full_name: str, customer_phone_number: str, address: str):
        self.customer_full_name = customer_full_name
        self.customer_phone_number = customer_phone_number
        self.address = address
        self.message = (
            f"Meter for customer '{customer_full_name}' with phone '{customer_phone_number}' "
            f"and address '{address}' already exists."
        )
        super().__init__(self.message) 


class MeterInactiveError(Exception):
    def __init__(self):
        self.message = f"Meter is inactive and cannot be used."
        super().__init__(self.message)


class MeterInUseError(Exception):
    def __init__(self):
        self.message = "Cannot delete meter with existing readings. Set status to inactive instead."
        super().__init__(self.message)
        

class NoActiveMetersError(Exception):
    def __init__(self):
        self.message = "No active meters found."
        super().__init__(self.message)


class InvalidColumnsException(Exception):
    def __init__(self, required_columns: list):
        self.required_columns = required_columns
        self.message = (
            f"Required columns {self.required_columns} not found in the provided data. "
        )
        super().__init__(self.message)


class EmptyFileException(Exception):
    def __init__(self, file_type: str):
        self.message = f"The provided {file_type} file is empty or contains no data rows."
        super().__init__(self.message)


class FileProcessingTimeoutException(Exception):
    def __init__(self, timeout: int):
        self.message = f"File processing exceeded the timeout of {timeout} seconds."
        self.timeout = timeout
        super().__init__(self.message)


class InitialReadingRequiredError(Exception):
    def __init__(self):
        self.message = f"Initial reading is required when switching from fixed to usage billing."
        super().__init__(self.message)
