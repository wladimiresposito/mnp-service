from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, Response

from app.config.settings import settings


def install_release_middlewares(app: FastAPI) -> None:
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def release_hardening_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.perf_counter()

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_body_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": "Request body too large.",
                    "request_id": request_id,
                },
            )

        try:
            response: Response = await call_next(request)
        except Exception:
            # Do not expose stack traces to clients.
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error.",
                    "request_id": request_id,
                },
            )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        if settings.enable_request_id:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-ms"] = str(duration_ms)

        if settings.enable_security_headers:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response
