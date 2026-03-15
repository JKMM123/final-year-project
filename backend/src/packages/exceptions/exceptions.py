


class PackagesNotFoundError(Exception):
    """Exception raised when a package is not found."""
    def __init__(self):
        self.message = f"Package not found."
        super().__init__(self.message)


class PackageAlreadyExistsError(Exception):
    """Exception raised when a package already exists."""
    def __init__(self, amperage: str):
        self.message = f"Package with amperage '{amperage}' already exists."
        super().__init__(self.message)


class PackageInUseError(Exception):
    """Exception raised when a package is in use."""
    def __init__(self, amperage: str):
        self.message = f"Package with amperage '{amperage}' is currently in use and cannot be deleted."
        super().__init__(self.message)

class InvalidPackageError(Exception):
    """Exception raised when a package is invalid."""
    def __init__(self, invalid_packages: list):
        self.message = f"Invalid packages found: {invalid_packages}"
        super().__init__(self.message)
