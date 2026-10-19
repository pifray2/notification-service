# notification-service

Микросервис уведомлений для CRM. Читает события из Kafka, складывает уведомления
в PostgreSQL и отдаёт их по HTTP.

## Что делает

- Подписывается на топик CRM `legal-entities-created` (создание юридического лица).
- Преобразует событие в уведомление: `event_type = "legal_entity_created"`,
  `message = "Создано новое юридическое лицо: {name}"`, `created_at` — время события из CRM.
- Хранит уведомления в собственной БД.

### Гарантии обработки

- **Идемпотентность.** `UNIQUE(event_type, entity_id)` + `INSERT ... ON CONFLICT DO NOTHING`:
  повторная доставка того же события не создаёт вторую запись.
- **Порядок коммитов.** Сначала коммит в БД, затем commit offset в Kafka. Падение между
  ними приводит к повторной доставке, которую гасит идемпотентность
  (at-least-once + идемпотентная запись ≈ exactly-once).
- **Poison-сообщения** (битый JSON, не проходит валидацию, неизвестный топик) логируются,
  offset коммитится, обработка продолжается — сервис не зацикливается.
- **Временные ошибки БД** не коммитят offset — сообщение будет переобработано после рестарта.

## Стек

Python 3.14, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic, confluent-kafka, PostgreSQL 18.

Слои: `app/api` (роуты) → `app/services` (логика) → `app/repositories` (SQL) → `app/models` (ORM).
Consumer запускается в `lifespan` FastAPI.

## Связь с CRM

Сервис не поднимает собственный брокер — использует Kafka из CRM по общей сети `shared-kafka`:

- внутри сети брокер доступен как `kafka:9092` (контейнер сервиса);
- с хоста — как `localhost:29092` (второй listener, для локальной разработки).

## Запуск

Требуются Docker и запущенный Kafka из `real-crm-project`.

```bash
# 1. Общая сеть (один раз)
docker network create shared-kafka

# 2. Kafka из CRM
cd ../real-crm-project && docker compose up -d kafka

# 3. Сервис уведомлений
cd ../notification-service
cp .env.example .env
docker compose up --build -d
```

Проверка:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/notifications
```

## API

| Метод | Путь | Описание |
|---|---|---|
| GET | `/health` | `200 {"status":"ok"}`; `503` — если БД недоступна |
| GET | `/notifications?limit=&offset=` | список уведомлений, новые первыми (`created_at desc`) |

`limit` — 1..1000 (по умолчанию 100), `offset` ≥ 0.

```json
[
  {
    "id": "af993424-9f78-4893-8a3c-f187133994c6",
    "event_type": "legal_entity_created",
    "entity_id": "2f5ab16c-7096-499d-ab0d-28e6dc4647c8",
    "message": "Создано новое юридическое лицо: OOO Extra",
    "created_at": "2026-10-19T15:04:10.728614Z"
  }
]
```

## Формат входного события (`legal-entities-created`)

```json
{
  "id": "9eecd64c-984f-47f7-822d-ca7433495c63",
  "created_at": "2026-10-13T11:25:51.405002+00:00",
  "company_id": "4cb67202-7b1e-47de-825a-1e819f41ca94",
  "name": "Peter"
}
```
Лишние поля игнорируются.

## Переменные окружения

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `DATABASE_URL` | DSN БД (asyncpg) | — |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | параметры контейнера БД | `notification-service` / `postgres` / `postgres` |
| `KAFKA_BROKERS` | адрес брокера | `kafka:9092` |
| `KAFKA_TOPIC` | топик-источник | `legal-entities-created` |
| `KAFKA_GROUP_ID` | consumer group | `notification-service` |
| `SQL_ECHO` | логировать SQL | `false` |
| `DEBUG` | уровень логов | `true` |

## Разработка на хосте

```bash
docker compose up -d db
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:55433/notification-service"
export KAFKA_BROKERS="localhost:29092"
python -m uvicorn app.main:app --port 8001
```

## Тесты

```bash
pip install -e ".[dev]"
docker compose up -d db            # тестам нужен Postgres
python -m pytest
```

Тестовая БД `notification-service-test` создаётся автоматически в том же контейнере.

## Ограничения

- Только топик `legal-entities-created`; `bank-accounts-created` и `reminders-due` — не реализованы.
- Нет аутентификации и пагинационных метаданных.
- Ребаланс consumer-группы и ретраи временных ошибок БД упрощены
  (полагаемся на at-least-once + идемпотентность).