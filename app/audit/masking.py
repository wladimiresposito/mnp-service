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

import hashlib
from typing import Any

from app.config.settings import settings

MASK = "***MASKED***"


def _minimize_text(text: str) -> dict[str, Any]:
    """Substitui texto livre por uma representacao minimizada e auditavel.

    Guarda: marcador, comprimento, e um SHA-256 com pepper por deployment.
    O hash permite provar depois que um texto especifico foi processado
    (comparando hashes), sem reter o conteudo sensivel no banco.
    """
    digest = hashlib.sha256(
        (settings.audit_text_hash_salt + text).encode("utf-8")
    ).hexdigest()
    return {
        "_minimized": True,
        "length": len(text),
        "sha256": digest,
    }


def mask_payload(value: Any) -> Any:
    if not settings.mask_sensitive_fields and not settings.minimize_free_text:
        return value
    return _mask(
        value,
        sensitive_fields=settings.sensitive_fields if settings.mask_sensitive_fields else set(),
        free_text_fields=settings.free_text_fields if settings.minimize_free_text else set(),
    )


def _mask(value: Any, sensitive_fields: set[str], free_text_fields: set[str]) -> Any:
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, item in value.items():
            key_lower = key.lower()
            if key_lower in sensitive_fields:
                masked[key] = MASK
            elif key_lower in free_text_fields and isinstance(item, str):
                masked[key] = _minimize_text(item)
            else:
                masked[key] = _mask(item, sensitive_fields, free_text_fields)
        return masked

    if isinstance(value, list):
        return [_mask(item, sensitive_fields, free_text_fields) for item in value]

    return value
