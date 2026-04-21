from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.core.config import (
    get_route_config,
    set_route_config,
    delete_route_config,
    get_all_configs
)

router = APIRouter(prefix="/admin", tags=["admin"])

class RouteConfigUpdate(BaseModel):
    limit: int | None = Field(None, description="Max requests allowed in window", example=100)
    window: int | None = Field(None, description="Window size in seconds", example=60)
    algorithm: str | None = Field(None, description="Algorithm: fixed, sliding, token_bucket", example="sliding")
    capacity: int | None = Field(None, description="Token bucket capacity (token_bucket only)", example=20)
    refill_rate: float | None = Field(None, description="Tokens per second (token_bucket only)", example=0.5)

class ConfigResponse(BaseModel):
    path: str
    config: dict

class AllConfigsResponse(BaseModel):
    configs: dict


@router.get(
    "/config",
    response_model=AllConfigsResponse,
    summary="List all rate limit configs",
    description="Returns merged view of all configs — Redis overrides take precedence over defaults."
)
async def list_all_configs():
    configs = await get_all_configs()
    return {"configs": configs}


@router.get(
    "/config/{path:path}",
    response_model=ConfigResponse,
    summary="Get config for a specific route",
    description="Fetch the active rate limit config for a route. Returns Redis override if set, otherwise returns default."
)
async def get_config(path: str):
    config = await get_route_config(f"/{path}")
    return {"path": f"/{path}", "config": config}


@router.post(
    "/config/{path:path}",
    response_model=ConfigResponse,
    summary="Update config for a route (hot-reload)",
    description="""
Update rate limit config for any route **without restarting the server**.

The change is saved to Redis and takes effect on the **very next request**
to that route across all running instances.

Example — change `/api/data` to use sliding window with limit 50:
```json
{
  "limit": 50,
  "window": 60,
  "algorithm": "sliding"
}
```
    """
)
async def update_config(path: str, body: RouteConfigUpdate):
    config = {k: v for k, v in body.model_dump().items() if v is not None}
    saved = await set_route_config(f"/{path}", config)
    return {
        "path": f"/{path}",
        "config": saved
    }


@router.delete(
    "/config/{path:path}",
    summary="Reset route config to default",
    description="Removes the Redis override for this route. Falls back to DEFAULT_CONFIG instantly."
)
async def reset_config(path: str):
    deleted = await delete_route_config(f"/{path}")
    return {
        "message": f"Config reset for /{path}",
        "deleted": deleted
    }