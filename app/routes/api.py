from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["rate-limited"])

class SuccessResponse(BaseModel):
    message: str
    client_ip: str

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "message": "Request successful",
                "client_ip": "127.0.0.1"
            }]
        }
    }

class RateLimitErrorResponse(BaseModel):
    error: str
    retry_after_seconds: int

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "error": "Too Many Requests",
                "retry_after_seconds": 45
            }]
        }
    }


@router.get(
    "/api/data",
    response_model=SuccessResponse,
    summary="Fixed window rate limited endpoint",
    description="""
Demonstrates **Fixed Window** rate limiting.

A counter is stored in Redis using `INCR`. When the window expires, 
the counter resets. Simple and fast but vulnerable to boundary bursts.

**Redis operations:** `INCR`, `EXPIRE`  
**Default limit:** 10 requests per 60 seconds
    """,
    responses={
        200: {"description": "Request allowed", "model": SuccessResponse},
        429: {"description": "Rate limit exceeded", "model": RateLimitErrorResponse}
    }
)
async def get_data(request: Request):
    return {
        "message": "Request successful",
        "client_ip": request.client.host
    }


@router.get(
    "/api/sliding",
    response_model=SuccessResponse,
    summary="Sliding window rate limited endpoint",
    description="""
Demonstrates **Sliding Window Log** rate limiting.

Each request is stored as a timestamped entry in a Redis sorted set.
On every request, entries older than the window are removed and the 
remaining count is checked. No boundary burst vulnerability.

**Redis operations:** `ZADD`, `ZREMRANGEBYSCORE`, `ZCARD`  
**Default limit:** 10 requests per 60 seconds
    """,
    responses={
        200: {"description": "Request allowed", "model": SuccessResponse},
        429: {"description": "Rate limit exceeded", "model": RateLimitErrorResponse}
    }
)
async def get_data_sliding(request: Request):
    return {
        "message": "Sliding window endpoint",
        "client_ip": request.client.host
    }


@router.get(
    "/api/bucket",
    response_model=SuccessResponse,
    summary="Token bucket rate limited endpoint",
    description="""
Demonstrates **Token Bucket** rate limiting.

Tokens accumulate over time at a fixed refill rate up to a maximum capacity.
Each request consumes one token. Allows controlled bursting — idle users 
can accumulate tokens and spend them all at once.

Implemented using an **atomic Lua script** in Redis to prevent race conditions
between token read and write operations.

**Redis operations:** Lua script (`GET`, `SET`, `EXPIRE`)  
**Default:** capacity=10, refill=0.1 tokens/second
    """,
    responses={
        200: {"description": "Request allowed", "model": SuccessResponse},
        429: {"description": "Rate limit exceeded", "model": RateLimitErrorResponse}
    }
)
async def get_data_bucket(request: Request):
    return {
        "message": "Token bucket endpoint",
        "client_ip": request.client.host
    }