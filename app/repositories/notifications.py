from sqlalchemy.dialects.postgresql import insert

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification
from sqlalchemy import select

class NotificationRepository:
    """ Notification's Repository """
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        
    async def save(self, n: Notification) -> Notification | None:
        query = insert(Notification).values(
            event_type=n.event_type, entity_id=n.entity_id,
            message=n.message, created_at=n.created_at,
        ).on_conflict_do_nothing(
            index_elements=["event_type", "entity_id"],
        ).returning(Notification)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list(self, *, limit, offset) -> list[Notification]:
        query = (
            select(Notification)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
