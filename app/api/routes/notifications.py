from fastapi import APIRouter, Depends, Query
from app.models import Notification
from app.schemas.notification import NotificationResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.notifications import NotificationRepository
from app.db.session import get_db_session
router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> list[Notification]:
    notification = NotificationRepository(session)
    rows = await notification.list(limit=limit, offset=offset)
    return [NotificationResponse.model_validate(r) for r in rows]
