import json
from app.core.redis_client import get_redis_client

# Default config — used when no Redis override exists
DEFAULT_CONFIG = {
    "/api/data": {
        "limit": 10,
        "window": 60,
        "algorithm": "fixed"
    },
    "/api/sliding": {
        "limit": 10,
        "window": 60,
        "algorithm": "sliding"
    },
    "/api/bucket": {
        "capacity": 10,
        "refill_rate": 0.1,
        "algorithm": "token_bucket"
    },
    "default": {
        "limit": 10,
        "window": 60,
        "algorithm": "fixed"
    }
}

async def get_route_config(path: str) -> dict:
    """
    Fetch config for a route. Checks Redis first (hot config),
    falls back to DEFAULT_CONFIG if not found.
    """
    redis = get_redis_client()

    # Try exact path match in Redis first
    redis_key = f"throttlex:config:{path}"
    cached = await redis.get(redis_key)

    if cached:
        return json.loads(cached)

    # Fall back to default config
    return DEFAULT_CONFIG.get(path) or DEFAULT_CONFIG["default"]


async def set_route_config(path: str, config: dict) -> dict:
    """
    Save a route config to Redis — takes effect immediately
    on all running instances without restart.
    """
    redis = get_redis_client()
    redis_key = f"throttlex:config:{path}"
    await redis.set(redis_key, json.dumps(config))
    return config


async def delete_route_config(path: str) -> bool:
    """
    Remove Redis override — route falls back to DEFAULT_CONFIG.
    """
    redis = get_redis_client()
    redis_key = f"throttlex:config:{path}"
    deleted = await redis.delete(redis_key)
    return bool(deleted)


async def get_all_configs() -> dict:
    """
    Returns merged view: defaults overridden by any Redis configs.
    """
    redis = get_redis_client()
    result = dict(DEFAULT_CONFIG)

    # Find all config keys in Redis
    keys = await redis.keys("throttlex:config:*")
    for key in keys:
        path = key.replace("throttlex:config:", "")
        value = await redis.get(key)
        if value:
            result[path] = json.loads(value)

    return result