"""
Database management with asyncpg for FastAPI
Provides connection pooling and async database operations
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncpg
from typing import Any, Dict, List, Optional
import logging

try:
    from config import Config, settings
except ImportError:
    from backend.config import Config, settings

logger = logging.getLogger(__name__)

# Legacy synchronous database (for backward compatibility)
def get_db_connection():
    """Create and return a synchronous database connection"""
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        cursor_factory=RealDictCursor
    )
    return conn

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query and optionally fetch results (synchronous)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = None
            
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# New async database connection pool
_pool: Optional[asyncpg.Pool] = None

async def init_db():
    """Initialize the async database connection pool"""
    global _pool
    try:
        _pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("✓ Database pool created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create database pool: {e}")
        raise

async def get_db_pool() -> asyncpg.Pool:
    """Get the database connection pool"""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")
    return _pool

async def close_db():
    """Close the database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("✓ Database pool closed")

async def execute_async(
    query: str,
    *args,
    fetch_one: bool = False,
    fetch_all: bool = False
) -> Any:
    """Execute an async database query"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        if fetch_one:
            return await conn.fetchrow(query, *args)
        elif fetch_all:
            return await conn.fetch(query, *args)
        else:
            return await conn.execute(query, *args)

async def transaction_context(conn: asyncpg.Connection):
    """Context manager for database transactions"""
    async with conn.transaction():
        yield conn
