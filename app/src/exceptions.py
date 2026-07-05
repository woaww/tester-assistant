from src.text_constants import LoggerMsg


class LLMInvalidResponseError(Exception):
    def __init__(self, message: str | None = None):
        self.message = message or LoggerMsg.ERROR
        super().__init__(self.message)
