from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LegalEntityCreatedEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: UUID
    company_id: UUID
    name: str = Field(min_length=1, max_length=100)
    created_at: datetime
    
