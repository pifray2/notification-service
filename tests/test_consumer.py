import json
from uuid import UUID

import pytest
from sqlalchemy import select

import app.db.session as db_session
from app.integrations.consumer import NotificationConsumer
from app.models import Notification


class FakeMessage:
    def __init__(self, value: bytes, *, topic="legal-entities-created",
                 partition=0, offset=0, error=None):
        self._value = value
        self._topic = topic
        self._partition = partition
        self._offset = offset
        self._error = error

    def value(self): return self._value
    def topic(self): return self._topic
    def partition(self): return self._partition
    def offset(self): return self._offset
    def error(self): return self._error


class FakeConsumer:
    def __init__(self, *args, **kwargs):
        self.committed = []

    async def commit(self, *args, message=None, **kwargs):
        self.committed.append(message)


@pytest.fixture
def consumer(monkeypatch):
    monkeypatch.setattr("app.integrations.consumer.AIOConsumer", FakeConsumer)
    monkeypatch.setattr("app.integrations.consumer.SessionLocal", db_session.SessionLocal)
    return NotificationConsumer()


async def test_valid_message_saves_and_commits(consumer, session, make_event_payload):
    payload = make_event_payload()
    await consumer._handle_message(FakeMessage(json.dumps(payload).encode()))

    assert len(consumer._consumer.committed) == 1
    rows = (await session.execute(select(Notification))).scalars().all()
    assert len(rows) == 1
    assert rows[0].entity_id == UUID(payload["id"])
    assert rows[0].message == f"Создано новое юридическое лицо: {payload['name']}"


async def test_duplicate_commits_without_second_row(consumer, session, make_event_payload):
    raw = json.dumps(make_event_payload()).encode()
    await consumer._handle_message(FakeMessage(raw))
    await consumer._handle_message(FakeMessage(raw))

    assert len(consumer._consumer.committed) == 2      # offset двигается оба раза
    rows = (await session.execute(select(Notification))).scalars().all()
    assert len(rows) == 1                              # но строка одна


async def test_bad_json_is_committed_and_skipped(consumer, session):
    await consumer._handle_message(FakeMessage(b"{not json"))

    assert len(consumer._consumer.committed) == 1      # poison -> коммитим, чтобы не зациклиться
    rows = (await session.execute(select(Notification))).scalars().all()
    assert rows == []


async def test_validation_error_is_committed_and_skipped(consumer, session, make_event_payload):
    payload = make_event_payload()
    payload.pop("name")
    await consumer._handle_message(FakeMessage(json.dumps(payload).encode()))

    assert len(consumer._consumer.committed) == 1
    rows = (await session.execute(select(Notification))).scalars().all()
    assert rows == []


async def test_transient_db_error_does_not_commit(consumer, monkeypatch, make_event_payload):
    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr("app.integrations.consumer.SessionLocal", boom)
    await consumer._handle_message(FakeMessage(json.dumps(make_event_payload()).encode()))

    assert consumer._consumer.committed == []          # временную ошибку НЕ коммитим