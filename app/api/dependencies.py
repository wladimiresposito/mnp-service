from fastapi import Header, HTTPException, status

from app.config.settings import settings


def require_api_key(x_mnp_api_key: str | None = Header(default=None)) -> None:
    if not settings.require_api_key:
        return

    if not x_mnp_api_key or x_mnp_api_key not in settings.allowed_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-MNP-API-Key.",
        )
