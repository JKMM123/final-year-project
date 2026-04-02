

class WhatsAppSessionNotFoundError(Exception):
    def __init__(self):
        self.message = "WhatsApp session not found."
        super().__init__(self.message)


class WhatsAppSessionAlreadyExistsError(Exception):
    def __init__(self):
        self.message = "WhatsApp session already exists."
        super().__init__(self.message)
