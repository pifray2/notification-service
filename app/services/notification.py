from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notifications import NotificationRepository
from app.models.notification import Notification
from app.schemas.events import LegalEntityCreatedEvent

TOPIC_TO_EVENT_TYPE = {"legal-entities-created": "legal_entity_created"}

class UnsupportedTopicError(Exception):
    pass

class NotificationService:
    
    def __init__(self, session:AsyncSession):
        self.session = session
        self.notifications = NotificationRepository(session)
    
    @staticmethod
    def create_notification(topic: str, payload: dict) -> Notification:
        if topic not in TOPIC_TO_EVENT_TYPE:
            raise UnsupportedTopicError(topic)
        event = LegalEntityCreatedEvent.model_validate(payload)
        return Notification(
        event_type=TOPIC_TO_EVENT_TYPE[topic],
        entity_id=event.id,
        message=f"Создано новое юридическое лицо: {event.name}",
        created_at=event.created_at,
    )
    
    async def list_notifications(self, *, limit: int, offset: int) -> list[Notification]:
        return await self.notifications.list(limit=limit, offset=offset)
    
    async def process_event(self, topic: str, payload: dict) -> Notification | None:
        event = self.create_notification(topic, payload)
        return await self.notifications.save(event)