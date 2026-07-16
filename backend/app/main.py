"""AttendIQ COA FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import get_settings
from .database import init_db
from .routers import (
    analytics,
    attendance,
    auth,
    courses,
    quizzes,
    resources,
    sessions,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Smart Attendance, Engagement, and Learning Rewards Platform (Phase 1 MVP).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Return errors in the standard API envelope."""
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        error = {"code": detail["code"], "details": detail.get("details")}
    else:
        error = {"code": f"HTTP_{exc.status_code}", "details": str(detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": error["details"], "error": error},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "error": {"code": "VALIDATION_ERROR", "details": str(exc.errors())},
        },
    )


@app.get("/health", tags=["meta"])
def health():
    return {"success": True, "message": "ok", "data": {"status": "healthy"}}


for _router in (
    auth.router,
    courses.router,
    sessions.router,
    attendance.router,
    quizzes.router,
    resources.router,
    analytics.router,
):
    app.include_router(_router, prefix=settings.api_prefix)
