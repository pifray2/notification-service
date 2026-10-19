from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: UUID
    event_type: str
    entity_id: UUID
    message: str
    created_at: datetime
    model_config = ConfigDict(from_attributes= True)