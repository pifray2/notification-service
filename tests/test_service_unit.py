from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.services.notification import NotificationService, UnsupportedTopicError


def _payload(**overrides) -> dict:
    base = {
        "id": str(uuid4()),
        "company_id": str(uuid4()),
        "name": "OOO Test",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    base.update(overrides)
    return base


def test_create_notification_maps_fields():
    payload = _payload()
    n = NotificationService.create_notification("legal-entities-created", payload)
    assert n.event_type == "legal_entity_created"
    assert n.entity_id == UUID(payload["id"])
    assert n.message == f"Создано новое юридическое лицо: {payload['name']}"
    assert n.created_at == datetime.fromisoformat(payload["created_at"])


def test_unknown_topic_raises():
    with pytest.raises(UnsupportedTopicError):
        NotificationService.create_notification("unknown-topic", _payload())