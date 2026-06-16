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
