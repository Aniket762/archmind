from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"Request failed: {method} {path} from {client_host}",
                exc_info=e
            )
            raise

        duration_ms = (time.time() - start_time) * 1000

        status_code = response.status_code
        logger.info(
            f"{method} {path} {status_code} {duration_ms:.1f}ms from {client_host}"
        )

        response.headers["X-Process-Time"] = str(duration_ms)

        return response


class ValidationErrorHandler:
    @staticmethod
    async def validation_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": str(exc),
            },
        )


def setup_middleware(app) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)