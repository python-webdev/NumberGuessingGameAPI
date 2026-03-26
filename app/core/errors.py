from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.types import ExceptionHandler


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors()[0]["msg"],
            "status_code": 422,
        },
    )


async def not_found_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Not Found",
            "details": exc.detail,
            "status_code": exc.status_code,
        },
    )


async def server_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "details": str(exc),
            "status_code": 500,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        RequestValidationError, cast(ExceptionHandler, validation_error_handler)
    )
    app.add_exception_handler(HTTPException, cast(ExceptionHandler, not_found_handler))
    app.add_exception_handler(Exception, cast(ExceptionHandler, server_error_handler))
