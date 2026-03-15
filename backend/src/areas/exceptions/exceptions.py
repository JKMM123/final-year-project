


class AreaAlreadyExistsException(Exception):
    def __init__(self, area_name: str):
        self.message = f"Area with name '{area_name}' already exists."
        super().__init__(self.message)


class AreaNotFoundException(Exception):
    def __init__(self):
        self.message = "Area not found."
        super().__init__(self.message)


class AreaLinkedToMetersException(Exception):
    def __init__(self, number_of_meters: int):
        self.message = f"Area is linked to {number_of_meters} meters and cannot be deleted."
        super().__init__(self.message)

class InvalidAreaNameException(Exception):
    def __init__(self, invalid_areas: list):
        self.message = f"Invalid area name(s): {', '.join(invalid_areas)}."
        super().__init__(self.message)
