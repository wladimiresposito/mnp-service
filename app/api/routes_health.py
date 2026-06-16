from fastapi import APIRouter

from app.core.version import version_info

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        **version_info(),
    }
