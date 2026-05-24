from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
 
from app.config import get_settings
from app.api.routes import architecture
from app.api.middleware import setup_middleware
from app.api.exceptions import AppException, ErrorResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="AI-Powered System Design Simulator",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug,
)

setup_middleware(app)

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code,
            detail=exc.message,
        ).model_dump(),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")
 
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            detail=f"Invalid input in '{field}': {message}",
        ).model_dump(),
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    import traceback
    traceback.print_exc()
 
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            detail="An unexpected error occurred",
        ).model_dump(),
    )

@app.get("/")
async def root() -> dict:
    return {
        "service": settings.app_name,
        "version": settings.api_version,
        "status": "ready",
        "docs": "/docs",
    }
 
 
@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}
 
app.include_router(
    architecture.router,
    prefix=f"/api/{settings.api_version}",
)
 
@app.on_event("startup")
async def startup_event():
    print(f"🚀 {settings.app_name} v{settings.api_version} started")
    if settings.debug:
        print("Running in DEBUG mode")
 
 
@app.on_event("shutdown")
async def shutdown_event():
    print(f"{settings.app_name} shutting down")