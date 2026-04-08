class FixNotFoundError(Exception):
    def __init__(self):
        self.message = "Fix not found."
        super().__init__(self.message)


class MeterNotFoundError(Exception):
    def __init__(self):
        self.message = "Meter not found."
        super().__init__(self.message)


class MeterInactiveError(Exception):
    def __init__(self):
        self.message = "Meter is inactive."
        super().__init__(self.message)


