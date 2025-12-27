"""
Redis client for caching and distributed locking
"""
import redis.asyncio as redis
import json
import logging
from typing import Any, Optional
from datetime import timedelta, datetime
from decimal import Decimal

try:
    from config import settings
except ImportError:
    from backend.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None

async def init_redis():
    """Initialize Redis connection"""
    global _redis_client
    try:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True
        )
        # Test connection
        await _redis_client.ping()
        logger.info("✓ Redis connected successfully")
    except Exception as e:
        logger.error(f"✗ Failed to connect to Redis: {e}")
        raise

async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("✓ Redis connection closed")

def get_redis() -> redis.Redis:
    """Get Redis client"""
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal and datetime objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Cache operations
async def cache_set(key: str, value: Any, ttl: int = 300):
    """Set a cache value with TTL"""
    client = get_redis()
    if isinstance(value, (dict, list)):
        value = json.dumps(value, cls=CustomJSONEncoder)
    await client.setex(key, ttl, value)

async def cache_get(key: str) -> Optional[Any]:
    """Get a cache value"""
    client = get_redis()
    value = await client.get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return None

async def cache_delete(key: str):
    """Delete a cache value"""
    client = get_redis()
    await client.delete(key)

async def cache_delete_pattern(pattern: str):
    """Delete all keys matching a pattern"""
    client = get_redis()
    keys = []
    async for key in client.scan_iter(match=pattern):
        keys.append(key)
    if keys:
        await client.delete(*keys)

# Distributed locking
async def acquire_lock(lock_key: str, ttl: int = 10) -> bool:
    """
    Acquire a distributed lock using Redis SETNX
    Returns True if lock acquired, False otherwise
    """
    client = get_redis()
    result = await client.set(lock_key, "1", nx=True, ex=ttl)
    return result is not None

async def release_lock(lock_key: str):
    """Release a distributed lock"""
    client = get_redis()
    await client.delete(lock_key)

async def acquire_lock_with_retry(
    lock_key: str,
    ttl: int = 10,
    max_attempts: int = 20,
    retry_delay: float = 0.05
) -> bool:
    """
    Try to acquire lock with retries
    """
    import asyncio
    for attempt in range(max_attempts):
        if await acquire_lock(lock_key, ttl):
            return True
        await asyncio.sleep(retry_delay)
    return False

# Idempotency
async def check_idempotency(key: str) -> Optional[dict]:
    """Check if an operation with this idempotency key was already processed"""
    return await cache_get(f"idempotency:{key}")

async def store_idempotency(key: str, result: dict, ttl: int = 86400):
    """Store idempotency result (24 hour TTL by default)"""
    await cache_set(f"idempotency:{key}", result, ttl)
