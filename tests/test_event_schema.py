from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas.events import LegalEntityCreatedEvent


def _payload(**overrides) -> dict:
    base = {
        "id": str(uuid4()),
        "company_id": str(uuid4()),
        "name": "OOO Test",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    base.update(overrides)
    return base


def test_valid_payload_parses():
    event = LegalEntityCreatedEvent.model_validate(_payload())
    assert isinstance(event.id, UUID)
    assert event.name == "OOO Test"


def test_missing_required_field_raises():
    payload = _payload()
    payload.pop("name")
    with pytest.raises(ValidationError):
        LegalEntityCreatedEvent.model_validate(payload)


def test_extra_fields_are_ignored():
    event = LegalEntityCreatedEvent.model_validate(_payload(company_name="x", extra=1))
    assert not hasattr(event, "company_name")