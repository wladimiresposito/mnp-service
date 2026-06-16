# Copyright 2026 Wladimir Esposito (OmniAI / Omni Tech Consulting)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
