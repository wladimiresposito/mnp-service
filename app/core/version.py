from __future__ import annotations

from app.config.settings import settings


def version_info() -> dict:
    return {
        "service": settings.service_name,
        "version": settings.version,
        "release_name": settings.release_name,
        "env": settings.env,
        "audit_backend": settings.audit_backend,
        "default_fact_extractor": settings.default_fact_extractor,
    }
