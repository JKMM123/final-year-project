class TemplateNotFoundError(Exception):
    def __init__(self, message: str = "Template not found."):
        super().__init__(message)
        self.message = message


class TemplateAlreadyExistsError(Exception):
    def __init__(self, message: str = "Template with this name and category already exists."):
        super().__init__(message)
        self.message = message


class InvalidAreasProvidedError(Exception):
    def __init__(self, invalid_areas: list):
        message = f"The following area IDs are invalid: {', '.join(invalid_areas)}"
        super().__init__(message)
        self.message = message


class InvalidPackagesProvidedError(Exception):
    def __init__(self, invalid_packages: list):
        message = f"The following package IDs are invalid: {', '.join(invalid_packages)}"
        super().__init__(message)
        self.message = message


class InvalidCustomersProvidedError(Exception):
    def __init__(self, invalid_customers: list):
        message = f"The following customer IDs are invalid: {', '.join(invalid_customers)}"
        super().__init__(message)
        self.message = message


