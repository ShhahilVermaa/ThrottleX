from fastapi import APIRouter
from pydantic import BaseModel
from app.core.redis_client import get_redis_client

router = APIRouter(tags=["health"])

class HealthResponse(BaseModel):
    status: str
    service: str
    redis: str

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "status": "ok",
                "service": "ThrottleX",
                "redis": "connected"
            }]
        }
    }

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service status and Redis connectivity. Use this to verify the system is running correctly."
)
async def health_check():
    redis = get_redis_client()
    try:
        await redis.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "unreachable"

    return {
        "status": "ok",
        "service": "ThrottleX",
        "redis": redis_status
    }