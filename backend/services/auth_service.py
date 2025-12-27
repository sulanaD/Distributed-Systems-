"""
Authentication service with JWT and bcrypt
Migrated from Flask to FastAPI with enhancements
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

from database import execute_async, get_db_pool
from config import settings
from cache.redis_client import cache_set, cache_get, cache_delete

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(password, password_hash)

# JWT token creation
def create_access_token(user_id: int, email: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None

# User operations
async def create_user(email: str, password: str, first_name: str, last_name: str) -> Optional[Dict]:
    """Create a new user in the database"""
    password_hash = hash_password(password)
    
    query = """
        INSERT INTO users (email, password_hash, first_name, last_name)
        VALUES ($1, $2, $3, $4)
        RETURNING id, email, first_name, last_name, is_active, created_at
    """
    
    try:
        user = await execute_async(
            query,
            email.lower().strip(),
            password_hash,
            first_name.strip(),
            last_name.strip(),
            fetch_one=True
        )
        if user:
            return dict(user)
        return None
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

async def get_user_by_email(email: str) -> Optional[Dict]:
    """Get a user by email"""
    query = "SELECT * FROM users WHERE email = $1"
    user = await execute_async(query, email.lower(), fetch_one=True)
    return dict(user) if user else None

async def get_user_by_id(user_id: int, use_cache: bool = True) -> Optional[Dict]:
    """Get a user by ID with optional caching"""
    if use_cache:
        cache_key = f"user:{user_id}"
        cached = await cache_get(cache_key)
        if cached:
            return cached
    
    query = "SELECT id, email, first_name, last_name, is_active, created_at FROM users WHERE id = $1"
    user = await execute_async(query, user_id, fetch_one=True)
    
    if user:
        user_dict = dict(user)
        if use_cache:
            await cache_set(f"user:{user_id}", user_dict, ttl=settings.CACHE_TTL_ACCOUNT)
        return user_dict
    return None

async def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """Authenticate a user by email and password"""
    user = await get_user_by_email(email)
    
    if user and verify_password(password, user['password_hash']):
        # Remove password hash from returned user
        del user['password_hash']
        return user
    
    return None

async def invalidate_user_cache(user_id: int):
    """Invalidate user cache"""
    await cache_delete(f"user:{user_id}")
