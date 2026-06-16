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

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import require_api_key
from app.review.models import ResolveHumanReviewRequest
from app.review.queue import human_review_queue

router = APIRouter(prefix="/human-review", tags=["human-review"])


@router.get("/pending")
def list_pending_reviews(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: None = Depends(require_api_key),
) -> dict:
    return human_review_queue.list(status="pending", limit=limit, offset=offset)


@router.get("")
def list_reviews(
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: None = Depends(require_api_key),
) -> dict:
    return human_review_queue.list(status=status, limit=limit, offset=offset)


@router.get("/{review_id}")
def get_review(review_id: str, _: None = Depends(require_api_key)) -> dict:
    record = human_review_queue.get(review_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Review item not found.")
    return record


@router.post("/{review_id}/resolve")
def resolve_review(
    review_id: str,
    payload: ResolveHumanReviewRequest,
    _: None = Depends(require_api_key),
) -> dict:
    record = human_review_queue.resolve(review_id, payload.resolution)
    if record is None:
        raise HTTPException(status_code=404, detail="Review item not found.")
    return record
