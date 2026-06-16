from fastapi import APIRouter, Depends

from app.api.dependencies import require_api_key
from app.core.registry import default_registry

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("")
def list_plugins(_: None = Depends(require_api_key)) -> dict:
    return {
        "plugins": [
            plugin.metadata().model_dump()
            for plugin in default_registry.all_plugins()
        ]
    }
