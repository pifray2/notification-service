import asyncio
import json
import logging

from confluent_kafka.aio import AIOConsumer
from confluent_kafka import Message
from pydantic import ValidationError
from app.core.config import get_settings
from app.services.notification import NotificationService, UnsupportedTopicError
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class NotificationConsumer():
    
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self._running = False
        self._consumer = AIOConsumer({
            "bootstrap.servers": self.settings.kafka_brokers,
            "group.id": self.settings.kafka_group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        self._task: asyncio.Task | None = None 
        
        
    async def start(self) -> None:
        await self._consumer.subscribe([self.settings.kafka_topic])
        self._running = True
        self._task = asyncio.create_task(self._loop())

    
    async def _loop(self) -> None:
        while self._running:
            msg: Message | None = await self._consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.warning("consumer error: %s", msg.error())
                continue
            await self._handle_message(msg)
        
            
    async def _handle_message(self, msg: Message) -> None:
        try:
            payload = json.loads(msg.value())
        except (json.JSONDecodeError, TypeError):
            logger.warning("bad message %s [%s] @ %s", msg.topic(), msg.partition(), msg.offset())
            await self._commit_offset(msg)
            return  
        try:
            async with SessionLocal() as session:
                service = NotificationService(session)
                notification = await service.process_event(msg.topic(), payload)
                await session.commit()
        except (ValidationError, UnsupportedTopicError) as exc:
            logger.warning("bad message %s [%s] @ %s: %s", msg.topic(), msg.partition(), msg.offset(), exc)
            await self._commit_offset(msg)
            return
        except Exception:
            logger.exception("transient error %s [%s] @ %s (offset NOT committed)", msg.topic(), msg.partition(), msg.offset())
            return

        await self._commit_offset(msg)
        if notification is None:
            logger.info("Duplicate skipped: %s", payload.get("id"))
        else:
            logger.info("saved notification: %s", notification.id)

            
    async def _commit_offset(self, msg: Message) -> None:
        await self._consumer.commit(message=msg, asynchronous=False)
    
    
    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            await self._task
        await self._consumer.close()
    