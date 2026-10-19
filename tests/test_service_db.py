from app.services.notification import NotificationService


async def test_process_event_saves(session, make_event_payload):
    svc = NotificationService(session)
    n = await svc.process_event("legal-entities-created", make_event_payload())
    await session.commit()
    assert n is not None
    assert n.event_type == "legal_entity_created"


async def test_process_event_duplicate_returns_none(session, make_event_payload):
    svc = NotificationService(session)
    payload = make_event_payload()
    assert await svc.process_event("legal-entities-created", payload) is not None
    await session.commit()
    assert await svc.process_event("legal-entities-created", payload) is None
    await session.commit()
