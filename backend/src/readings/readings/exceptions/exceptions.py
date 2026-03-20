class ReadingNotFoundException(Exception):
    def __init__(self):
        self.message = f"Reading not found."
        super().__init__(self.message)


class InvalidReadingValueException(Exception):
    def __init__(self, current_reading: float, previous_reading: float):
        self.message = f"Current reading ({current_reading}) cannot be less than previous reading ({previous_reading})."
        self.current_reading = current_reading
        self.previous_reading = previous_reading
        super().__init__(self.message)


class ReadingAlreadyVerifiedException(Exception):
    def __init__(self):
        self.message = f"Reading is already verified and cannot be modified."
        super().__init__(self.message)


class ReadingFrequencyException(Exception):
    def __init__(self, current_reading_date: str, allowed_date_range: tuple):
        self.message = (
            f"Current reading date '{current_reading_date}' must be within "
            f"{allowed_date_range[0]} and {allowed_date_range[1]}."
        )
        self.current_reading_date = current_reading_date
        self.allowed_date_range = allowed_date_range
        super().__init__(self.message)
        

class DuplicateReadingDateException(Exception):
    def __init__(self, reading_date: str):
        self.message = f"A reading for this meter already exists for current month on '{reading_date}'."
        self.reading_date = reading_date
        super().__init__(self.message)


class NoReadingsFoundForActiveMetersError(Exception):
    def __init__(self, date: str):
        self.message = f"No readings found for active meters on {date}."
        self.date = date
        super().__init__(self.message)


class MissingReadingsForActiveMetersError(Exception):
    def __init__(self, date: str, number_of_meters: int):
        self.message = f"Missing readings for {number_of_meters} active meters on {date}."
        self.date = date
        self.number_of_meters = number_of_meters
        super().__init__(self.message)
        

class UnverifiedReadingsError(Exception):
    def __init__(self, date: str, number_of_unverified_readings: int):
        self.message = f"There is {number_of_unverified_readings} unverified readings for active meters on {date}."
        self.date = date
        self.number_of_unverified_readings = number_of_unverified_readings
        super().__init__(self.message)


class FixedMeterCannotHaveUsageReadingsError(Exception):
    def __init__(self):
        self.message = f"Fixed meters cannot have usage readings."
        super().__init__(self.message)

        