from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import health, api, admin
from app.core.redis_client import redis_pool
from app.middleware.rate_limit import RateLimitMiddleware
import redis.asyncio as aioredis

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        await client.ping()
        print("✅ Redis connected successfully")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
    yield
    await redis_pool.disconnect()
    print("🔌 Redis pool disconnected")


app = FastAPI(
    title="ThrottleX",
    description="""
## Distributed Rate Limiting System

ThrottleX is a production-grade rate limiting API built with **FastAPI** and **Redis**.
It supports three rate limiting algorithms, hot-reloadable config, and is designed
to work across multiple distributed backend instances.

---

### Algorithms supported

| Algorithm | Redis Structure | Best for |
|---|---|---|
| Fixed Window | String + INCR | Simple APIs, low traffic |
| Sliding Window | Sorted Set + ZCARD | Accurate per-user limits |
| Token Bucket | Lua script + GET/SET | Bursty traffic, cloud APIs |

---

### Rate limit headers

Every response includes:
- `X-RateLimit-Limit` — max requests allowed
- `X-RateLimit-Remaining` — requests left in current window
- `Retry-After` — seconds to wait (only on 429 responses)

---

### Load test results
- **160 RPS** sustained with 50 concurrent users
- **p99 latency: 23ms** under full load
- **Zero 500 errors** — Redis atomic operations held under concurrency
    """,
    version="1.0.0",
    contact={
        "name": "ThrottleX",
        "url": "https://github.com/yourusername/throttlex",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "System health and Redis connectivity checks."
        },
        {
            "name": "rate-limited",
            "description": """
Test endpoints demonstrating each rate limiting algorithm.
All responses include `X-RateLimit-*` headers showing current limit state.
            """
        },
        {
            "name": "admin",
            "description": """
Hot-reload configuration endpoints. Update rate limits **without restarting** the server.
Changes take effect immediately across all running instances.
⚠️ In production these would be protected by API key authentication.
            """
        }
    ],
    lifespan=lifespan
)

app.add_middleware(RateLimitMiddleware)
app.include_router(health.router)
app.include_router(api.router)
app.include_router(admin.router)