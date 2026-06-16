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

import hashlib

from app.audit.masking import mask_payload
from app.config.settings import settings


def test_free_text_user_text_is_minimized_not_stored_raw():
    sensitive = "Tenho uma mancha na pele e uso corticoide. Meu CPF e 123."
    payload = {
        "context": {
            "user_text": sensitive,
            "facts": {"contains_sensitive_health_data": True},
        }
    }
    masked = mask_payload(payload)
    user_text = masked["context"]["user_text"]

    # O texto bruto nao pode aparecer em lugar nenhum da estrutura mascarada.
    assert sensitive not in str(masked)
    # Deve virar uma representacao minimizada e auditavel.
    assert user_text["_minimized"] is True
    assert user_text["length"] == len(sensitive)
    expected = hashlib.sha256(
        (settings.audit_text_hash_salt + sensitive).encode("utf-8")
    ).hexdigest()
    assert user_text["sha256"] == expected


def test_draft_text_is_minimized():
    payload = {"draft": {"text": "Pode usar a pomada, e seguro."}}
    masked = mask_payload(payload)
    assert masked["draft"]["text"]["_minimized"] is True


def test_key_name_masking_still_applies():
    payload = {"authorization": "Bearer abc", "cpf": "12345678900"}
    masked = mask_payload(payload)
    assert masked["authorization"] == "***MASKED***"
    assert masked["cpf"] == "***MASKED***"


def test_same_text_same_hash_audit_provenance():
    a = mask_payload({"user_text": "mesma frase"})
    b = mask_payload({"user_text": "mesma frase"})
    # Determinismo: permite provar que o mesmo texto foi processado.
    assert a["user_text"]["sha256"] == b["user_text"]["sha256"]


def test_facts_dict_is_preserved_for_audit():
    # Fatos estruturados (nao texto livre) continuam visiveis para auditoria.
    payload = {"facts": {"contains_sensitive_health_data": True, "domain": "healthcare"}}
    masked = mask_payload(payload)
    assert masked["facts"]["contains_sensitive_health_data"] is True
    assert masked["facts"]["domain"] == "healthcare"
