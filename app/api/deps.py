from fastapi import Depends
from app.db.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.notification import NotificationService


def get_notifications_service(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationService:
    return NotificationService(session)