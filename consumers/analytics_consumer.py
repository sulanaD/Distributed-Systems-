"""
Analytics Consumer - Aggregates transaction metrics in real-time
Calculates statistics for monitoring and business intelligence
"""
import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from datetime import datetime
from collections import defaultdict
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from backend.cache.redis_client import init_redis, get_redis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AnalyticsConsumer:
    def __init__(self):
        self.consumer = None
        self.running = False
        
        # In-memory aggregation (resets on restart)
        self.stats = {
            'total_transactions': 0,
            'completed_transactions': 0,
            'failed_transactions': 0,
            'total_volume': 0.0,
            'total_fees': 0.0,
            'hourly_transactions': defaultdict(int),
            'account_updates': 0
        }
        
    async def start(self):
        """Initialize consumer and Redis"""
        logger.info("📊 Starting Analytics Consumer...")
        
        # Initialize Redis for storing aggregated metrics
        await init_redis()
        logger.info("✓ Redis initialized")
        
        # Create Kafka consumer
        self.consumer = AIOKafkaConsumer(
            'transactions.completed',
            'transactions.failed',
            'account.updates',
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id='analytics-consumer-group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        await self.consumer.start()
        logger.info("✓ Kafka consumer started")
        logger.info("📈 Calculating real-time transaction analytics")
        
        self.running = True
        
    async def stop(self):
        """Stop consumer gracefully"""
        logger.info("Stopping Analytics Consumer...")
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        
        # Log final statistics
        self.print_statistics()
        logger.info("✓ Analytics Consumer stopped")
        
    def print_statistics(self):
        """Print current statistics"""
        logger.info("=" * 60)
        logger.info("TRANSACTION ANALYTICS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Transactions: {self.stats['total_transactions']}")
        logger.info(f"  ✓ Completed: {self.stats['completed_transactions']}")
        logger.info(f"  ✗ Failed: {self.stats['failed_transactions']}")
        logger.info(f"Total Volume: ${self.stats['total_volume']:.2f}")
        logger.info(f"Total Fees Collected: ${self.stats['total_fees']:.2f}")
        logger.info(f"Account Updates: {self.stats['account_updates']}")
        
        if self.stats['total_transactions'] > 0:
            success_rate = (self.stats['completed_transactions'] / self.stats['total_transactions']) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")
            
            if self.stats['completed_transactions'] > 0:
                avg_transaction = self.stats['total_volume'] / self.stats['completed_transactions']
                avg_fee = self.stats['total_fees'] / self.stats['completed_transactions']
                logger.info(f"Average Transaction: ${avg_transaction:.2f}")
                logger.info(f"Average Fee: ${avg_fee:.2f}")
        
        logger.info("=" * 60)
        
    async def store_metric_in_redis(self, key: str, value: any):
        """Store metric in Redis for persistence"""
        try:
            redis_client = get_redis()
            await redis_client.set(f"analytics:{key}", str(value), ex=86400)  # 24h TTL
        except Exception as e:
            logger.error(f"Failed to store metric in Redis: {e}")
            
    async def process_transaction_completed(self, event: dict):
        """Process completed transaction metrics"""
        self.stats['total_transactions'] += 1
        self.stats['completed_transactions'] += 1
        
        amount = float(event.get('amount', 0))
        fee = float(event.get('fee', 0))
        
        self.stats['total_volume'] += amount
        self.stats['total_fees'] += fee
        
        # Track hourly transactions
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        self.stats['hourly_transactions'][current_hour] += 1
        
        # Store in Redis
        await self.store_metric_in_redis('completed_transactions', self.stats['completed_transactions'])
        await self.store_metric_in_redis('total_volume', self.stats['total_volume'])
        await self.store_metric_in_redis('total_fees', self.stats['total_fees'])
        
        # Log periodic updates
        if self.stats['completed_transactions'] % 10 == 0:
            logger.info(f"📊 Milestone: {self.stats['completed_transactions']} completed transactions")
            logger.info(f"   Total Volume: ${self.stats['total_volume']:.2f}")
            logger.info(f"   Total Fees: ${self.stats['total_fees']:.2f}")
        
    async def process_transaction_failed(self, event: dict):
        """Process failed transaction metrics"""
        self.stats['total_transactions'] += 1
        self.stats['failed_transactions'] += 1
        
        error = event.get('error', 'Unknown')
        
        # Store in Redis
        await self.store_metric_in_redis('failed_transactions', self.stats['failed_transactions'])
        
        # Track failure reasons
        failure_key = f"failure_reason:{error[:50]}"
        redis_client = get_redis()
        try:
            await redis_client.incr(f"analytics:{failure_key}")
        except:
            pass
            
        logger.warning(f"⚠️  Transaction failed: {error}")
        
    async def process_account_update(self, event: dict):
        """Process account update metrics"""
        self.stats['account_updates'] += 1
        
        # Store in Redis
        await self.store_metric_in_redis('account_updates', self.stats['account_updates'])
    
    async def run(self):
        """Main consumer loop"""
        try:
            await self.start()
            
            # Print stats every 60 seconds
            stats_task = asyncio.create_task(self.periodic_stats())
            
            async for message in self.consumer:
                try:
                    topic = message.topic
                    event = message.value
                    
                    logger.debug(f"Processing analytics for {topic}")
                    
                    if topic == 'transactions.completed':
                        await self.process_transaction_completed(event)
                    elif topic == 'transactions.failed':
                        await self.process_transaction_failed(event)
                    elif topic == 'account.updates':
                        await self.process_account_update(event)
                    
                except Exception as e:
                    logger.error(f"Error processing analytics: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            await self.stop()
            
    async def periodic_stats(self):
        """Print statistics periodically"""
        while self.running:
            await asyncio.sleep(60)  # Every 60 seconds
            if self.stats['total_transactions'] > 0:
                self.print_statistics()

if __name__ == "__main__":
    consumer = AnalyticsConsumer()
    asyncio.run(consumer.run())
