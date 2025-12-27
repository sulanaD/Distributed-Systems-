"""
Account service for banking operations with caching
"""
import random
import logging
from typing import Optional, Dict, List
from decimal import Decimal

from database import execute_async, get_db_pool
from cache.redis_client import cache_set, cache_get, cache_delete, cache_delete_pattern
from config import settings

logger = logging.getLogger(__name__)

def generate_account_number(user_id: int) -> str:
    """Generate a unique account number"""
    prefix = f"ACC{user_id}"
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    return f"{prefix}{suffix}"

async def create_account(
    user_id: int,
    account_type: str = "savings",
    initial_balance: Decimal = Decimal("0.00")
) -> Optional[Dict]:
    """Create a new bank account"""
    account_number = generate_account_number(user_id)
    
    query = """
        INSERT INTO accounts (user_id, account_number, account_type, balance)
        VALUES ($1, $2, $3, $4)
        RETURNING id, user_id, account_number, account_type, balance, currency, is_active, created_at
    """
    
    try:
        account = await execute_async(
            query,
            user_id,
            account_number,
            account_type,
            initial_balance,
            fetch_one=True
        )
        if account:
            account_dict = dict(account)
            # Cache the new account
            await cache_set(f"account:{account_number}", account_dict, ttl=settings.CACHE_TTL_ACCOUNT)
            return account_dict
        return None
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        return None

async def get_account_by_number(account_number: str, use_cache: bool = True) -> Optional[Dict]:
    """Get account by account number with caching"""
    if use_cache:
        cache_key = f"account:{account_number}"
        cached = await cache_get(cache_key)
        if cached:
            return cached
    
    query = """
        SELECT id, user_id, account_number, account_type, balance, currency, is_active, created_at
        FROM accounts
        WHERE account_number = $1
    """
    account = await execute_async(query, account_number, fetch_one=True)
    
    if account:
        account_dict = dict(account)
        if use_cache:
            await cache_set(f"account:{account_number}", account_dict, ttl=settings.CACHE_TTL_ACCOUNT)
        return account_dict
    return None

async def get_account_by_id(account_id: int) -> Optional[Dict]:
    """Get account by ID"""
    query = """
        SELECT id, user_id, account_number, account_type, balance, currency, is_active, created_at
        FROM accounts
        WHERE id = $1
    """
    account = await execute_async(query, account_id, fetch_one=True)
    return dict(account) if account else None

async def get_user_accounts(user_id: int) -> List[Dict]:
    """Get all accounts for a user"""
    query = """
        SELECT id, user_id, account_number, account_type, balance, currency, is_active, created_at
        FROM accounts
        WHERE user_id = $1 AND is_active = true
        ORDER BY created_at DESC
    """
    accounts = await execute_async(query, user_id, fetch_all=True)
    return [dict(acc) for acc in accounts]

async def get_account_balance(account_number: str, use_cache: bool = True) -> Optional[Decimal]:
    """Get account balance with caching"""
    if use_cache:
        cache_key = f"balance:{account_number}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return Decimal(str(cached))
    
    query = "SELECT balance FROM accounts WHERE account_number = $1 AND is_active = true"
    result = await execute_async(query, account_number, fetch_one=True)
    
    if result:
        balance = result['balance']
        if use_cache:
            await cache_set(f"balance:{account_number}", float(balance), ttl=settings.CACHE_TTL_BALANCE)
        return balance
    return None

async def update_account_balance(account_id: int, new_balance: Decimal):
    """Update account balance and invalidate cache"""
    query = "UPDATE accounts SET balance = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
    await execute_async(query, new_balance, account_id)
    
    # Get account number to invalidate cache
    account = await get_account_by_id(account_id)
    if account:
        account_number = account['account_number']
        await cache_delete(f"balance:{account_number}")
        await cache_delete(f"account:{account_number}")

async def invalidate_account_cache(account_number: str):
    """Invalidate all caches related to an account"""
    await cache_delete(f"balance:{account_number}")
    await cache_delete(f"account:{account_number}")

async def delete_account(account_number: str, user_id: int) -> bool:
    """Delete an account (soft delete by setting is_active to false)"""
    # Get account first to verify ownership and check balance
    account = await get_account_by_number(account_number, use_cache=False)
    
    if not account:
        raise ValueError("Account not found")
    
    if account['user_id'] != user_id:
        raise ValueError("You don't have permission to delete this account")
    
    # Check if account has balance
    if account['balance'] > 0:
        raise ValueError("Cannot delete account with positive balance. Please transfer funds first.")
    
    # Soft delete - set is_active to false
    query = "UPDATE accounts SET is_active = false, updated_at = CURRENT_TIMESTAMP WHERE account_number = $1 AND user_id = $2"
    
    try:
        await execute_async(query, account_number, user_id)
        # Invalidate caches
        await invalidate_account_cache(account_number)
        logger.info(f"Account {account_number} deleted successfully")
        return True
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        return False
