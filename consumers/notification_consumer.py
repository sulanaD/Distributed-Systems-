"""
Notification Consumer - Sends notifications for transaction events
Simulates email/SMS/push notifications (logs for now)
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationConsumer:
    def __init__(self):
        self.consumer = None
        self.running = False
        
    async def start(self):
        """Initialize consumer"""
        logger.info("📧 Starting Notification Consumer...")
        
        # Create Kafka consumer
        self.consumer = AIOKafkaConsumer(
            'transactions.completed',
            'transactions.failed',
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id='notification-consumer-group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        await self.consumer.start()
        logger.info("✓ Kafka consumer started")
        logger.info("📬 Listening for transaction events to send notifications")
        
        self.running = True
        
    async def stop(self):
        """Stop consumer gracefully"""
        logger.info("Stopping Notification Consumer...")
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("✓ Notification Consumer stopped")
        
    async def send_notification(self, notification_type: str, recipient: str, message: str):
        """
        Send notification (simulated - logs for now)
        In production, integrate with email service (SendGrid, SES), SMS (Twilio), or push notifications
        """
        logger.info(f"📨 [{notification_type.upper()}] To: {recipient}")
        logger.info(f"   Message: {message}")
        
        # Simulate async operation
        await asyncio.sleep(0.1)
        
        # TODO: Implement actual notification sending
        # Examples:
        # - Email: await send_email(recipient, "Transaction Alert", message)
        # - SMS: await send_sms(recipient, message)
        # - Push: await send_push_notification(user_id, message)
        
    async def process_transaction_completed(self, event: dict):
        """Send notification for successful transaction"""
        from_account = event.get('from_account_number', 'Unknown')
        to_account = event.get('to_account_number', 'Unknown')
        amount = event.get('amount', 0)
        fee = event.get('fee', 0)
        transaction_id = event.get('transaction_id', 'N/A')
        
        # Notification for sender
        sender_message = (
            f"✅ Transfer Successful\n"
            f"Amount: ${amount:.2f}\n"
            f"Fee: ${fee:.2f}\n"
            f"To: {to_account}\n"
            f"Transaction ID: {transaction_id}"
        )
        await self.send_notification('email', from_account, sender_message)
        
        # Notification for recipient
        recipient_message = (
            f"💰 Money Received\n"
            f"Amount: ${amount:.2f}\n"
            f"From: {from_account}\n"
            f"Transaction ID: {transaction_id}"
        )
        await self.send_notification('email', to_account, recipient_message)
        
    async def process_transaction_failed(self, event: dict):
        """Send notification for failed transaction"""
        from_account = event.get('from_account_number', 'Unknown')
        to_account = event.get('to_account_number', 'Unknown')
        amount = event.get('amount', 0)
        error = event.get('error', 'Unknown error')
        transaction_id = event.get('transaction_id', 'N/A')
        
        # Notification for sender
        sender_message = (
            f"❌ Transfer Failed\n"
            f"Amount: ${amount:.2f}\n"
            f"To: {to_account}\n"
            f"Reason: {error}\n"
            f"Transaction ID: {transaction_id}\n"
            f"Please try again or contact support."
        )
        await self.send_notification('email', from_account, sender_message)
    
    async def run(self):
        """Main consumer loop"""
        try:
            await self.start()
            
            async for message in self.consumer:
                try:
                    topic = message.topic
                    event = message.value
                    
                    logger.debug(f"Received event from {topic}: {event}")
                    
                    if topic == 'transactions.completed':
                        await self.process_transaction_completed(event)
                    elif topic == 'transactions.failed':
                        await self.process_transaction_failed(event)
                    
                except Exception as e:
                    logger.error(f"Error processing notification: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            await self.stop()

if __name__ == "__main__":
    consumer = NotificationConsumer()
    asyncio.run(consumer.run())
