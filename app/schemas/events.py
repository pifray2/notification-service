from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LegalEntityCreatedEvent(BaseModel):
    id: UUID
    company_id: UUID
    name: str = Field(min_length=1, max_length=100)
    created_at: datetime
    
