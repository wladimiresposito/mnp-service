from __future__ import annotations

from functools import lru_cache

from app.audit.postgres_repository import PostgresAuditRepository
from app.audit.repository import AuditRepository
from app.audit.sqlite_repository import SQLiteAuditRepository
from app.config.settings import settings


@lru_cache(maxsize=1)
def get_audit_repository() -> AuditRepository:
    backend = settings.audit_backend.lower().strip()

    if backend == "sqlite":
        repo: AuditRepository = SQLiteAuditRepository(settings.sqlite_path)
    elif backend == "postgres":
        repo = PostgresAuditRepository(settings.postgres_dsn)
    else:
        raise ValueError(f"Unsupported MNP_AUDIT_BACKEND: {settings.audit_backend}")

    return repo


def init_audit_repository() -> None:
    get_audit_repository().init_db()
