"""
Kafka producer for event streaming
"""
from aiokafka import AIOKafkaProducer
import json
import logging
from typing import Optional, Dict, Any

from config import settings

logger = logging.getLogger(__name__)

_producer: Optional[AIOKafkaProducer] = None

async def init_kafka():
    """Initialize Kafka producer"""
    global _producer
    try:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip',
            acks='all'
        )
        await _producer.start()
        logger.info("✓ Kafka producer started successfully")
    except Exception as e:
        logger.error(f"✗ Failed to start Kafka producer: {e}")
        # Don't raise - Kafka is optional for basic functionality
        _producer = None

async def close_kafka():
    """Close Kafka producer"""
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
        logger.info("✓ Kafka producer stopped")

def get_producer() -> Optional[AIOKafkaProducer]:
    """Get Kafka producer"""
    return _producer

async def publish_event(topic: str, event: Dict[str, Any], key: Optional[str] = None):
    """Publish an event to Kafka"""
    producer = get_producer()
    if producer is None:
        logger.warning(f"Kafka not available, skipping event: {topic}")
        return
    
    try:
        key_bytes = key.encode('utf-8') if key else None
        await producer.send(topic, value=event, key=key_bytes)
        logger.debug(f"Published event to {topic}: {event}")
    except Exception as e:
        logger.error(f"Failed to publish event to {topic}: {e}")

# Specific event publishers
async def publish_transaction_completed(transaction: Dict[str, Any]):
    """Publish transaction completed event"""
    await publish_event(
        'transactions.completed',
        transaction,
        key=transaction.get('transaction_id')
    )

async def publish_transaction_failed(transaction: Dict[str, Any], error: str):
    """Publish transaction failed event"""
    await publish_event(
        'transactions.failed',
        {**transaction, 'error': error},
        key=transaction.get('transaction_id')
    )

async def publish_account_updated(account_id: int, balance: float):
    """Publish account updated event"""
    await publish_event(
        'account.updates',
        {'account_id': account_id, 'balance': balance},
        key=str(account_id)
    )
