from app.services.notification import NotificationService


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_list_notifications_empty(client):
    r = await client.get("/notifications")
    assert r.status_code == 200
    assert r.json() == []


async def test_list_notifications_returns_saved(client, session, make_event_payload):
    payload = make_event_payload()
    svc = NotificationService(session)
    await svc.process_event("legal-entities-created", payload)
    await session.commit()

    r = await client.get("/notifications")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert set(data[0]) == {"id", "event_type", "entity_id", "message", "created_at"}
    assert data[0]["entity_id"] == payload["id"]
    assert data[0]["message"] == f"Создано новое юридическое лицо: {payload['name']}"