from fastapi import APIRouter, Depends

from app.api.dependencies import require_api_key
from app.asp.engine import RULES_PATH, clingo_available, temporal_consent_engine
from app.asp.models import TemporalAspInput, TemporalAspResult

router = APIRouter(prefix="/asp", tags=["asp"])


@router.get("/status")
def asp_status(_: None = Depends(require_api_key)) -> dict:
    return {
        "clingo_available": clingo_available(),
        "rules_path": str(RULES_PATH),
        "plugin_id": "lgpd_temporal_asp",
        "mode": "clingo" if clingo_available() else "python_fallback",
    }


@router.post("/temporal-consent", response_model=TemporalAspResult)
def evaluate_temporal_consent(
    payload: TemporalAspInput,
    _: None = Depends(require_api_key),
) -> TemporalAspResult:
    return temporal_consent_engine.evaluate(payload)
