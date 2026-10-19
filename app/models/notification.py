from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class Notification(UUIDPrimaryKeyMixin, Base):
    """ Notification's data """
    
    __tablename__ = "notifications"
    
    __table_args__ = (UniqueConstraint("event_type", "entity_id", name="uq_notification_event_entity"),)

    entity_id: Mapped[UUID] = mapped_column(Uuid)
    event_type: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

