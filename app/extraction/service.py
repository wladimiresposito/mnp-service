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

from pydantic import ValidationError

from app.config.settings import settings
from app.extraction.base import FactExtractor
from app.extraction.heuristic_extractor import HeuristicFactExtractor
from app.extraction.llm_extractor import LLMExtractionError, MockLLMFactExtractor, OpenAICompatibleFactExtractor
from app.extraction.models import FactExtractionRequest, FactExtractionResponse, NormativeFacts
from app.review.queue import human_review_queue


def get_fact_extractor(mode: str | None) -> FactExtractor:
    selected = (mode or settings.default_fact_extractor).strip().lower()

    if selected == "heuristic":
        return HeuristicFactExtractor()
    if selected == "llm_mock":
        return MockLLMFactExtractor()
    if selected == "openai_compatible":
        return OpenAICompatibleFactExtractor()

    raise ValueError(f"Unknown fact extractor mode: {selected}")


def extract_and_validate(payload: FactExtractionRequest) -> FactExtractionResponse:
    threshold = (
        payload.low_confidence_threshold
        if payload.low_confidence_threshold is not None
        else settings.fact_confidence_threshold
    )

    mode = payload.mode or settings.default_fact_extractor
    validation_errors: list[str] = []
    raw_output: str | None = None

    try:
        extractor = get_fact_extractor(mode)
        facts, raw_output = extractor.extract(payload.user_text)
        valid = True
    except (ValidationError, LLMExtractionError, ValueError) as exc:
        valid = False
        validation_errors.append(str(exc))
        facts = NormativeFacts(
            domain="unknown",
            request_type="unknown",
            fact_extraction_confidence=0.0,
            uncertainty_reasons=["Extractor failed or returned invalid JSON."],
            evidence=[],
        )

    confidence = facts.fact_extraction_confidence
    requires_review = False
    fallback_reason = None

    if not valid:
        requires_review = True
        fallback_reason = "fact_extraction_validation_failed"
    elif confidence < threshold:
        requires_review = True
        fallback_reason = "low_fact_extraction_confidence"

    review_id = None
    if requires_review and payload.enqueue_human_review_on_fallback:
        review_id = human_review_queue.enqueue(
            reason=fallback_reason or "human_review_required",
            payload={
                "tenant_id": payload.tenant_id,
                "session_id": payload.session_id,
                "user_id": payload.user_id,
                "user_text": payload.user_text,
                "mode": mode,
                "facts": facts.model_dump(mode="json"),
                "confidence": confidence,
                "threshold": threshold,
                "validation_errors": validation_errors,
                "raw_model_output": raw_output,
            },
        )

    return FactExtractionResponse(
        tenant_id=payload.tenant_id,
        session_id=payload.session_id,
        user_id=payload.user_id,
        mode=mode,
        facts=facts,
        valid=valid,
        confidence=confidence,
        low_confidence_threshold=threshold,
        requires_human_review=requires_review,
        fallback_reason=fallback_reason,
        review_id=review_id,
        raw_model_output=raw_output,
        validation_errors=validation_errors,
    )
