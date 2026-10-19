from fastapi import APIRouter, Depends, Query
from app.api.deps import get_notifications_service
from app.models import Notification
from app.schemas.notification import NotificationResponse
from app.services.notification import NotificationService
router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: NotificationService = Depends(get_notifications_service),
) -> list[Notification]:
    rows = await service.list_notifications(limit=limit, offset=offset)
    return [NotificationResponse.model_validate(r) for r in rows]
