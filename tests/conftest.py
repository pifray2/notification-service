import asyncio
import os

TEST_DB_NAME = "notification-service-test"
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:55433/notification-service-test"
)

# ВАЖНО: подменяем URL ДО импорта app-модулей.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import asyncpg  
import pytest  
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402
from uuid import uuid4  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

import app.db.session as db_session  # noqa: E402
from app.db.base import metadata  # noqa: E402
from app.main import app  # noqa: E402

ADMIN_DSN = "postgresql://postgres:postgres@localhost:55433/postgres"


async def _ensure_database() -> None:
    conn = await asyncpg.connect(ADMIN_DSN)
    try:
        exists = await conn.fetchval(
            "select 1 from pg_database where datname = $1", TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_db() -> None:
    asyncio.run(_ensure_database())


@pytest.fixture(autouse=True)
async def _schema(_ensure_test_db):
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    db_session.engine = engine
    db_session.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture
async def session() -> AsyncSession:
    async with db_session.SessionLocal() as s:
        yield s


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def make_event_payload():
    def _make(**overrides) -> dict:
        base = {
            "id": str(uuid4()),
            "company_id": str(uuid4()),
            "name": "OOO Test",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        base.update(overrides)
        return base

    return _make
