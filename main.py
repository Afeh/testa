import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.core.config import settings
from api.utils.logger import logger
from api.v1.routes import api_router

from api.utils.json_response import JsonResponseDict

import traceback


@asynccontextmanager
async def lifespan(app: FastAPI):
	yield

app = FastAPI(lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5473",
    "http://localhost:5474",
    "http://localhost:5475",
    "https://ican-testa-examhack.vercel.app"
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/heartbeat")
def heartbeat():
    """Health check endpoint with model status."""
    # To check if the model is loaded

    logger.info(
        "Returning API Status",
        extra={
            "status": "ok",
            "version": "v1.0",
            "endpoint": "/heartbeat",

        },
    )
    return JsonResponseDict(
        message="Testa API up",
        status_code=status.HTTP_200_OK,
	)

# REGISTER EXCEPTION HANDLERS

@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": exc.detail
        }
    )

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Rate limit exceeded exception handler"""
    return JSONResponse(
        status_code=429,
        content={
            "status": False,
            "status_code": exc.status_code,
            "message": "Too many requests. Please try again in 60 seconds.",
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    def sanitize_errors(errors):
        for err in errors:
            if "ctx" in err and isinstance(err["ctx"], dict):
                # Replace non-serializable values in ctx
                err["ctx"] = {
                    k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v
                    for k, v in err["ctx"].items()
                }
        return errors

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "status_code": 422,
            "message": "Invalid input",
            "errors": sanitize_errors(exc.errors())
        }
    )

@app.exception_handler(Exception)
async def exception(request: Request, exc: Exception):
    logger.exception(f'Exception occured; {exc}')

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status_code": 500,
            "message": f"An unexpected error occurred: {exc}"
        }
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=settings.APP_PORT, reload=True)