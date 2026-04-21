import time
import uuid
from app.core.redis_client import get_redis_client


async def is_rate_limited(identifier: str, limit: int, window_seconds: int) -> dict:
    redis = get_redis_client()
    key = f"throttlex:{identifier}"

    async with redis.pipeline(transaction=True) as pipe:
        await pipe.incr(key)
        await pipe.expire(key, window_seconds)
        results = await pipe.execute()

    current_count = results[0]
    ttl = await redis.ttl(key)

    return {
        "allowed": current_count <= limit,
        "current_count": current_count,
        "limit": limit,
        "remaining": max(0, limit - current_count),
        "retry_after": ttl if current_count > limit else None
    }


async def is_rate_limited_sliding(identifier: str, limit: int, window_seconds: int) -> dict:
    redis = get_redis_client()
    key = f"throttlex:sliding:{identifier}"
    now = time.time()
    window_start = now - window_seconds

    async with redis.pipeline(transaction=True) as pipe:
        await pipe.zremrangebyscore(key, 0, window_start)
        await pipe.zcard(key)
        await pipe.zadd(key, {str(uuid.uuid4()): now})
        await pipe.expire(key, window_seconds)
        results = await pipe.execute()

    current_count = results[1]
    allowed = current_count < limit

    return {
        "allowed": allowed,
        "current_count": current_count + 1,
        "limit": limit,
        "remaining": max(0, limit - current_count - 1),
        "retry_after": window_seconds if not allowed else None
    }


TOKEN_BUCKET_SCRIPT = """
local key_tokens = KEYS[1]
local key_timestamp = KEYS[2]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local last_tokens = tonumber(redis.call('GET', key_tokens))
local last_refill = tonumber(redis.call('GET', key_timestamp))

if last_tokens == nil then
    last_tokens = capacity
end
if last_refill == nil then
    last_refill = now
end

local elapsed = now - last_refill
local new_tokens = last_tokens + (elapsed * refill_rate)

if new_tokens > capacity then
    new_tokens = capacity
end

local allowed = 0
if new_tokens >= requested then
    new_tokens = new_tokens - requested
    allowed = 1
end

redis.call('SET', key_tokens, tostring(new_tokens))
redis.call('SET', key_timestamp, tostring(now))
redis.call('EXPIRE', key_tokens, 3600)
redis.call('EXPIRE', key_timestamp, 3600)

return { allowed, tostring(new_tokens) }
"""


async def is_rate_limited_token_bucket(
    identifier: str,
    capacity: int = 10,
    refill_rate: float = 0.5
) -> dict:
    redis = get_redis_client()
    key_tokens = f"throttlex:tb:tokens:{identifier}"
    key_timestamp = f"throttlex:tb:ts:{identifier}"
    now = time.time()

    result = await redis.eval(
        TOKEN_BUCKET_SCRIPT,
        2,
        key_tokens,
        key_timestamp,
        str(capacity),
        str(refill_rate),
        str(now),
        str(1)
    )

    allowed = bool(result[0])
    tokens_remaining = round(float(result[1]), 2)

    return {
        "allowed": allowed,
        "tokens_remaining": tokens_remaining,
        "capacity": capacity,
        "refill_rate": refill_rate,
        "retry_after": None if allowed else round(1 / refill_rate, 2)
    }