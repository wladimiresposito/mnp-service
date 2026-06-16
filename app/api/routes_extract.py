from fastapi import APIRouter, Depends

from app.api.dependencies import require_api_key
from app.extraction.models import FactExtractionRequest, FactExtractionResponse, FactSchemaResponse, NormativeFacts
from app.extraction.prompt import SYSTEM_PROMPT
from app.extraction.service import extract_and_validate

router = APIRouter(prefix="/extract", tags=["extraction"])


@router.get("/schema", response_model=FactSchemaResponse)
def get_fact_schema(_: None = Depends(require_api_key)) -> FactSchemaResponse:
    return FactSchemaResponse(
        json_schema=NormativeFacts.model_json_schema(),
        instruction=SYSTEM_PROMPT,
    )


@router.post("/facts", response_model=FactExtractionResponse)
def extract_facts(
    payload: FactExtractionRequest,
    _: None = Depends(require_api_key),
) -> FactExtractionResponse:
    return extract_and_validate(payload)
