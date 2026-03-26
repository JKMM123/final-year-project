class BillNotFoundError(Exception):
    def __init__(self):
        self.message = f"Bill not found."
        super().__init__(self.message)


class BillAlreadyExistsError(Exception):
    def __init__(self, due_date):
        self.message = f"Bills for due date {due_date} already generated."
        super().__init__(self.message)


class BillsGenerationRestrictionError(Exception):
    def __init__(self):
        self.message = "Bills can only be generated between the 1st and 5th of each month."
        super().__init__(self.message)


class DeletePaidBillError(Exception):
    def __init__(self, status):
        self.message = f"Can't delete a bill that has already been {status}."
        super().__init__(self.message)


class MessagesSendingError(Exception):
    def __init__(self):
        self.message = "Messages can only be sent between the 1st and 5th of each month."
        super().__init__(self.message)

