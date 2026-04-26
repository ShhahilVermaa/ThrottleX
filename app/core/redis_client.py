import redis.asyncio as aioredis
from dotenv import load_dotenv
import os

load_dotenv()

redis_url = os.getenv("REDIS_URL")

if redis_url:
    redis_pool = aioredis.ConnectionPool.from_url(
        redis_url,
        max_connections=20,
        decode_responses=True
    )
else:
    redis_pool = aioredis.ConnectionPool(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        password=os.getenv("REDIS_PASSWORD", None),
        max_connections=20,
        decode_responses=True
    )

def get_redis_client() -> aioredis.Redis:
    return aioredis.Redis(connection_pool=redis_pool)