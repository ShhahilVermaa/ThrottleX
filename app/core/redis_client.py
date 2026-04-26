import redis.asyncio as aioredis
from dotenv import load_dotenv
import os

load_dotenv()

# Connection pool created ONCE at module load time
redis_pool = aioredis.ConnectionPool(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    password=os.getenv("REDIS_PASSWORD", None),  # ← add this line
    max_connections=20,
    decode_responses=True
)

def get_redis_client() -> aioredis.Redis:
    """Returns a Redis client using the shared connection pool."""
    return aioredis.Redis(connection_pool=redis_pool)