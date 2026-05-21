from fastapi import Request
from fastapi.responses import JSONResponse


class AutoPITAException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AutoPITAException):
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status_code=404)


class UnauthorizedError(AutoPITAException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ConflictError(AutoPITAException):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ValidationError(AutoPITAException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


async def autopita_exception_handler(request: Request, exc: AutoPITAException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status_code": exc.status_code}
    )