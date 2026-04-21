from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.rate_limiter import (
    is_rate_limited,
    is_rate_limited_sliding,
    is_rate_limited_token_bucket
)
from app.core.config import get_route_config

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        if request.url.path in ("/health", ) or \
           request.url.path.startswith("/admin"):
            return await call_next(request)

        x_user_id = request.headers.get("X-User-ID")
        client_ip = request.client.host
        identifier = f"user_{x_user_id}" if x_user_id else f"ip_{client_ip}"
        path = request.url.path

        # Fetch config from Redis or fall back to defaults
        config = await get_route_config(path)
        algorithm = config.get("algorithm", "fixed")

        if algorithm == "sliding":
            result = await is_rate_limited_sliding(
                identifier,
                limit=config["limit"],
                window_seconds=config["window"]
            )
            remaining_key = "remaining"
            limit_val = config["limit"]

        elif algorithm == "token_bucket":
            result = await is_rate_limited_token_bucket(
                identifier,
                capacity=config.get("capacity", 10),
                refill_rate=config.get("refill_rate", 0.1)
            )
            remaining_key = "tokens_remaining"
            limit_val = config.get("capacity", 10)

        else:
            result = await is_rate_limited(
                identifier,
                limit=config["limit"],
                window_seconds=config["window"]
            )
            remaining_key = "remaining"
            limit_val = config["limit"]

        if not result["allowed"]:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "retry_after_seconds": result["retry_after"]
                },
                headers={
                    "Retry-After": str(result["retry_after"]),
                    "X-RateLimit-Limit": str(limit_val),
                    "X-RateLimit-Remaining": "0"
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit_val)
        response.headers["X-RateLimit-Remaining"] = str(result[remaining_key])
        return response