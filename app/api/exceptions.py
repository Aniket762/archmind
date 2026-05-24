from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    detail: str
    request_id: str | None = None


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(message)


class ValidationException(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
        )


class NotFoundException(AppException):
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
        )


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
        )


class InternalException(AppException):
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            message=message,
            status_code=500,
            error_code="INTERNAL_ERROR",
        )


class AIException(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=500,
            error_code="AI_ERROR",
        )


class InvalidGraphException(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVALID_GRAPH",
        )