"""
Audit Consumer - Listens to all Kafka events and writes audit trail to database
Provides compliance tracking and event history
"""
import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from backend.database import init_db, get_db_pool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuditConsumer:
    def __init__(self):
        self.consumer = None
        self.running = False
        
    async def start(self):
        """Initialize consumer and database"""
        logger.info("🔍 Starting Audit Consumer...")
        
        # Initialize database
        await init_db()
        logger.info("✓ Database initialized")
        
        # Create Kafka consumer
        self.consumer = AIOKafkaConsumer(
            'transactions.completed',
            'transactions.failed',
            'account.updates',
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id='audit-consumer-group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        await self.consumer.start()
        logger.info("✓ Kafka consumer started")
        logger.info("📝 Listening for events: transactions.completed, transactions.failed, account.updates")
        
        self.running = True
        
    async def stop(self):
        """Stop consumer gracefully"""
        logger.info("Stopping Audit Consumer...")
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("✓ Audit Consumer stopped")
        
    async def process_event(self, topic: str, event: dict):
        """Process and store audit event"""
        pool = await get_db_pool()
        
        try:
            async with pool.acquire() as conn:
                # Determine event details based on topic
                if topic == 'transactions.completed':
                    action = 'TRANSACTION_COMPLETED'
                    resource_type = 'transaction'
                    resource_id = event.get('transaction_id')
                    details = {
                        'from': event.get('from_account_number'),
                        'to': event.get('to_account_number'),
                        'amount': event.get('amount'),
                        'fee': event.get('fee'),
                        'status': 'completed'
                    }
                elif topic == 'transactions.failed':
                    action = 'TRANSACTION_FAILED'
                    resource_type = 'transaction'
                    resource_id = event.get('transaction_id')
                    details = {
                        'from': event.get('from_account_number'),
                        'to': event.get('to_account_number'),
                        'amount': event.get('amount'),
                        'error': event.get('error'),
                        'status': 'failed'
                    }
                elif topic == 'account.updates':
                    action = 'ACCOUNT_BALANCE_UPDATED'
                    resource_type = 'account'
                    resource_id = str(event.get('account_id'))
                    details = {
                        'account_id': event.get('account_id'),
                        'new_balance': event.get('balance')
                    }
                else:
                    action = 'UNKNOWN_EVENT'
                    resource_type = 'unknown'
                    resource_id = 'N/A'
                    details = event
                
                # Insert into audit_log table
                await conn.execute(
                    """
                    INSERT INTO audit_log (user_id, action, resource_type, resource_id, details)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    None,  # user_id not available from Kafka events
                    action,
                    resource_type,
                    resource_id,
                    json.dumps(details)
                )
                
                logger.info(f"✓ Audited: {action} - {resource_type}:{resource_id}")
                
        except Exception as e:
            logger.error(f"✗ Failed to audit event: {e}")
            logger.error(f"Event: {event}")
    
    async def run(self):
        """Main consumer loop"""
        try:
            await self.start()
            
            async for message in self.consumer:
                try:
                    topic = message.topic
                    event = message.value
                    
                    logger.debug(f"Received event from {topic}: {event}")
                    await self.process_event(topic, event)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            await self.stop()

if __name__ == "__main__":
    consumer = AuditConsumer()
    asyncio.run(consumer.run())
