from src.text_constants import LoggerMsg


class SpecificationParserErrorRead(Exception):

    def __init__(self):
        self.message = LoggerMsg.SPEC_API_READ_ERROR
        super().__init__(self.message)

class SpecificationParserErrorParse(Exception):

    def __init__(self):
        self.message = LoggerMsg.SPEC_API_PARSE_ERROR
        super().__init__(self.message)

class SpecificationParserEmptyError(Exception):

    def __init__(self):
        self.message = LoggerMsg.SPEC_API_PARSE_ERROR_EMPTY
        super().__init__(self.message)

# class SpecificationParserError(Exception):

#     def __init__(self):
#         self.message = LoggerMsg.ERROR
#         super().__init__(self.message)


class TestItParserError(Exception):

    def __init__(self):
        self.message = LoggerMsg.ERROR
        super().__init__(self.message)

class TestItAddSectionError(Exception):

    def __init__(self):
        self.message = LoggerMsg.ERROR
        super().__init__(self.message)

class TestItAddCaseError(Exception):

    def __init__(self):
        self.message = LoggerMsg.ERROR
        super().__init__(self.message)


class LLMInvalidResponseError(Exception):
    def __init__(self, message: str | None = None):
        self.message = message or LoggerMsg.ERROR
        super().__init__(self.message)
