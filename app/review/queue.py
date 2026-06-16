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

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.review.models import HumanReviewRecord


class JsonlHumanReviewQueue:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def enqueue(self, reason: str, payload: dict[str, Any]) -> str:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        review_id = str(uuid.uuid4())
        record = HumanReviewRecord(
            review_id=review_id,
            status="pending",
            reason=reason,
            payload=payload,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")
        return review_id

    def list(self, status: str | None = None, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        records = self._read_all()
        if status:
            records = [record for record in records if record.status == status]

        records = sorted(records, key=lambda r: r.created_at, reverse=True)
        return {
            "total": len(records),
            "limit": limit,
            "offset": offset,
            "items": [r.model_dump(mode="json") for r in records[offset:offset + limit]],
        }

    def get(self, review_id: str) -> dict[str, Any] | None:
        for record in self._read_all():
            if record.review_id == review_id:
                return record.model_dump(mode="json")
        return None

    def resolve(self, review_id: str, resolution: dict[str, Any]) -> dict[str, Any] | None:
        records = self._read_all()
        found = None

        for idx, record in enumerate(records):
            if record.review_id == review_id:
                updated = record.model_copy(
                    update={
                        "status": "resolved",
                        "resolution": resolution,
                        "resolved_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                records[idx] = updated
                found = updated
                break

        if found is None:
            return None

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(record.model_dump_json() + "\n")

        return found.model_dump(mode="json")

    def _read_all(self) -> list[HumanReviewRecord]:
        if not self.path.exists():
            return []

        records = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                records.append(HumanReviewRecord.model_validate_json(line))
        return records


human_review_queue = JsonlHumanReviewQueue(settings.human_review_path)
