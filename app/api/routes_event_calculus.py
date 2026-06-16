from fastapi import APIRouter, Depends

from app.api.dependencies import require_api_key
from app.event_calculus.engine import RULES_DIR, clingo_available, event_calculus_engine
from app.event_calculus.models import ECResult, ECScenario

router = APIRouter(prefix="/event-calculus", tags=["event-calculus"])


@router.get("/status")
def event_calculus_status(_: None = Depends(require_api_key)) -> dict:
    return {
        "clingo_available": clingo_available(),
        "rules_dir": str(RULES_DIR),
        "plugin_id": "lgpd_event_calculus",
        "mode": "clingo_event_calculus" if clingo_available() else "python_event_calculus_fallback",
        "modules": [
            "00_domain.lp",
            "10_event_calculus.lp",
            "20_lgpd_fluents.lp",
            "30_obligations.lp",
            "40_exceptions.lp",
            "50_consequences.lp",
        ],
    }


@router.post("/evaluate", response_model=ECResult)
def event_calculus_evaluate(
    payload: ECScenario,
    _: None = Depends(require_api_key),
) -> ECResult:
    return event_calculus_engine.evaluate(payload)
