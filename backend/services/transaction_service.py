"""
Transaction service with fee tiers, distributed locking, and Kafka events
"""
import uuid
import json
import logging
from typing import Optional, Dict, List, Tuple
from decimal import Decimal
from datetime import datetime

from database import get_db_pool
from cache.redis_client import (
    acquire_lock_with_retry,
    release_lock,
    check_idempotency,
    store_idempotency
)
from kafka.producer import publish_transaction_completed, publish_transaction_failed, publish_account_updated
from services.account_service import get_account_by_number, invalidate_account_cache

logger = logging.getLogger(__name__)

# Fee tier configuration
FEE_TIERS = [
    {"min": 0, "max": 2000, "percentage": 0.0, "cap": 0},
    {"min": 2000.01, "max": 10000, "percentage": 0.25, "cap": 20},
    {"min": 10000.01, "max": 20000, "percentage": 0.20, "cap": 25},
    {"min": 20000.01, "max": 50000, "percentage": 0.125, "cap": 40},
    {"min": 50000.01, "max": 100000, "percentage": 0.08, "cap": 50},
    {"min": 100000.01, "max": float('inf'), "percentage": 0.05, "cap": 100}
]

def calculate_fee(amount: Decimal) -> Decimal:
    """
    Calculate transfer fee based on tiered structure
    $0-$2,000: 0%
    $2,000.01-$10,000: 0.25%, capped at $20
    $10,000.01-$20,000: 0.20%, capped at $25
    $20,000.01-$50,000: 0.125%, capped at $40
    $50,000.01-$100,000: 0.08%, capped at $50
    $100,000.01+: 0.05%, capped at $100
    """
    amount_float = float(amount)
    
    for tier in FEE_TIERS:
        if tier["min"] <= amount_float <= tier["max"]:
            fee = amount * Decimal(str(tier["percentage"] / 100))
            cap = Decimal(str(tier["cap"]))
            return min(fee, cap) if cap > 0 else fee
    
    return Decimal("0")

async def process_transfer(
    from_account_number: str,
    to_account_number: str,
    amount: Decimal,
    user_id: int,
    description: Optional[str] = None,
    idempotency_key: Optional[str] = None
) -> Dict:
    """
    Process a transfer with distributed locking, fee calculation, and event streaming
    """
    # Validate accounts
    if from_account_number == to_account_number:
        raise ValueError("Cannot transfer to the same account")
    
    # Check idempotency
    if idempotency_key:
        cached_result = await check_idempotency(idempotency_key)
        if cached_result:
            logger.info(f"Returning cached result for idempotency key: {idempotency_key}")
            return cached_result
    
    # Get accounts
    from_account = await get_account_by_number(from_account_number, use_cache=False)
    to_account = await get_account_by_number(to_account_number, use_cache=False)
    
    if not from_account:
        raise ValueError(f"Source account {from_account_number} not found")
    if not to_account:
        raise ValueError(f"Destination account {to_account_number} not found")
    if not from_account['is_active']:
        raise ValueError("Source account is not active")
    if not to_account['is_active']:
        raise ValueError("Destination account is not active")
    if from_account['user_id'] != user_id:
        raise ValueError("You don't own the source account")
    
    # Calculate fee
    fee = calculate_fee(amount)
    total_amount = amount + fee
    
    # Check sufficient balance
    if from_account['balance'] < total_amount:
        raise ValueError(f"Insufficient balance. Required: ${total_amount}, Available: ${from_account['balance']}")
    
    # Acquire distributed lock for both accounts (prevent race conditions)
    lock_key = f"transfer:lock:{min(from_account['id'], to_account['id'])}:{max(from_account['id'], to_account['id'])}"
    
    if not await acquire_lock_with_retry(lock_key, ttl=10):
        raise RuntimeError("Failed to acquire transfer lock. Please try again.")
    
    try:
        # Execute transfer in database transaction
        transaction_id = str(uuid.uuid4())
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Deduct from source account
                await conn.execute(
                    "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
                    total_amount, from_account['id']
                )
                
                # Add to destination account
                await conn.execute(
                    "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
                    amount, to_account['id']
                )
                
                # Record transaction
                transaction = await conn.fetchrow(
                    """
                    INSERT INTO transactions 
                    (transaction_id, from_account_id, to_account_id, amount, fee, total_amount, status, description, idempotency_key)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING *
                    """,
                    transaction_id,
                    from_account['id'],
                    to_account['id'],
                    amount,
                    fee,
                    total_amount,
                    'completed',
                    description,
                    idempotency_key
                )
                
                # Audit log
                await conn.execute(
                    """
                    INSERT INTO audit_log (user_id, action, resource_type, resource_id, details)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    user_id,
                    'TRANSFER',
                    'transaction',
                    transaction_id,
                    json.dumps({
                        'from': from_account_number,
                        'to': to_account_number,
                        'amount': str(amount),
                        'fee': str(fee)
                    })
                )
        
        # Invalidate caches
        await invalidate_account_cache(from_account_number)
        await invalidate_account_cache(to_account_number)
        
        # Prepare response
        result = {
            "transaction_id": transaction_id,
            "from_account_number": from_account_number,
            "to_account_number": to_account_number,
            "amount": float(amount),
            "fee": float(fee),
            "total_amount": float(total_amount),
            "status": "completed",
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store idempotency result
        if idempotency_key:
            await store_idempotency(idempotency_key, result)
        
        # Publish Kafka events (non-blocking)
        try:
            await publish_transaction_completed(result)
            await publish_account_updated(from_account['id'], float(from_account['balance'] - total_amount))
            await publish_account_updated(to_account['id'], float(to_account['balance'] + amount))
        except Exception as e:
            logger.error(f"Failed to publish Kafka events: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        # Publish failed event
        try:
            await publish_transaction_failed({
                "from_account_number": from_account_number,
                "to_account_number": to_account_number,
                "amount": float(amount)
            }, str(e))
        except Exception as kafka_error:
            logger.error(f"Failed to publish failed event: {kafka_error}")
        raise
    finally:
        # Always release the lock
        await release_lock(lock_key)

async def get_transaction_history(user_id: int, limit: int = 50) -> List[Dict]:
    """Get transaction history for user's accounts"""
    pool = await get_db_pool()
    query = """
        SELECT t.*, 
               fa.account_number as from_account_number,
               ta.account_number as to_account_number
        FROM transactions t
        LEFT JOIN accounts fa ON t.from_account_id = fa.id
        LEFT JOIN accounts ta ON t.to_account_id = ta.id
        WHERE fa.user_id = $1 OR ta.user_id = $1
        ORDER BY t.created_at DESC
        LIMIT $2
    """
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, user_id, limit)
        return [dict(row) for row in rows]
