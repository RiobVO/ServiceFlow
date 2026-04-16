"""arq-воркер: периодический drain outbox_events.

Запуск:
    arq app.workers.arq_worker.WorkerSettings

По cron каждую секунду (низкая задержка, но дешёво) забираем пачку
непроцессированных событий под SKIP LOCKED и «публикуем» их — пока
просто структурный лог, позже сюда ляжет реальная шина/webhook/email.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import ClassVar

from arq.connections import RedisSettings
from arq.cron import cron

from app.core.logging import configure_logging, get_logger
from app.uow import SqlAlchemyUnitOfWork

configure_logging()
_log = get_logger("outbox_worker")


async def drain_outbox(ctx: dict) -> None:
    """Забираем пачку pending-событий и помечаем processed_at."""
    with SqlAlchemyUnitOfWork() as uow:
        batch = uow.outbox.fetch_pending(limit=100)
        if not batch:
            return

        for event in batch:
            # TODO(next): реальная публикация наружу (Kafka, webhook, email).
            _log.info(
                "outbox_event_published",
                event_id=event.id,
                event_type=event.event_type,
                payload=event.payload,
            )
            event.processed_at = datetime.utcnow()

        uow.commit()
        _log.info("outbox_batch_processed", size=len(batch))


async def on_startup(ctx: dict) -> None:
    _log.info("arq_worker_starting")


async def on_shutdown(ctx: dict) -> None:
    _log.info("arq_worker_stopping")


class WorkerSettings:
    redis_settings: ClassVar = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://redis:6379/0")
    )
    cron_jobs: ClassVar = [
        # каждую секунду
        cron(drain_outbox, second=set(range(0, 60))),
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = 5
