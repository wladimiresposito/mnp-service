from __future__ import annotations

import re
from typing import Any

from app.extraction.base import FactExtractor
from app.extraction.models import NormativeFacts


HEALTH_TERMS = [
    "mancha", "pele", "coceira", "dor", "sangramento", "pomada",
    "corticoide", "remédio", "medicamento", "diagnóstico", "tratamento",
    "febre", "diabetes", "pressão", "alergia",
]

LEGAL_TERMS = [
    "processo", "advogado", "contrato", "ação judicial", "jurídico",
    "direito", "indenização", "lei", "liminar",
]

FINANCE_TERMS = [
    "crédito", "empréstimo", "investimento", "juros", "financiamento",
    "seguro", "renda", "banco",
]

HR_TERMS = [
    "candidato", "currículo", "contratar", "demitir", "salário",
    "entrevista", "vaga",
]

MEDICATION_TERMS = ["pomada", "corticoide", "remédio", "medicamento", "antibiótico"]

URGENT_TERMS = ["falta de ar", "desmaio", "sangramento intenso", "dor intensa", "febre alta"]

PERSONAL_DATA_PATTERNS = [
    r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",  # CPF-like
    r"\b\S+@\S+\.\S+\b",                # email-like
    r"\+?55?\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}",  # BR phone-like
]


def extract_normative_facts(user_text: str, confidence: float | None = None) -> dict[str, Any]:
    facts, _ = HeuristicFactExtractor(default_confidence=confidence or 0.83).extract(user_text)
    return facts.model_dump(mode="json")


class HeuristicFactExtractor(FactExtractor):
    mode = "heuristic"

    def __init__(self, default_confidence: float = 0.83) -> None:
        self.default_confidence = default_confidence

    def extract(self, user_text: str) -> tuple[NormativeFacts, str | None]:
        text = user_text.lower()

        contains_health_data = any(term in text for term in HEALTH_TERMS)
        mentions_medication = any(term in text for term in MEDICATION_TERMS)
        asks_for_permission = bool(re.search(r"\b(posso|devo|pode|recomenda|usar|faço|fazer)\b", text))
        has_urgent_symptoms = any(term in text for term in URGENT_TERMS)

        contains_legal = any(term in text for term in LEGAL_TERMS)
        contains_finance = any(term in text for term in FINANCE_TERMS)
        contains_hr = any(term in text for term in HR_TERMS)

        contains_personal_data = any(re.search(pattern, user_text, flags=re.IGNORECASE) for pattern in PERSONAL_DATA_PATTERNS)

        domain = "general"
        if contains_health_data:
            domain = "healthcare"
        elif contains_legal:
            domain = "legal"
        elif contains_finance:
            domain = "finance"
        elif contains_hr:
            domain = "hr"

        request_type = "general_information"
        if contains_health_data and asks_for_permission:
            request_type = "clinical_recommendation"
        elif contains_legal and asks_for_permission:
            request_type = "legal_advice"
        elif contains_finance and asks_for_permission:
            request_type = "financial_advice"

        uncertainty_reasons = []
        confidence = self.default_confidence

        if domain == "general" and asks_for_permission:
            confidence = min(confidence, 0.68)
            uncertainty_reasons.append("Request asks for permission but domain is unclear.")

        if len(user_text.strip()) < 12:
            confidence = min(confidence, 0.55)
            uncertainty_reasons.append("Very short message.")

        facts = NormativeFacts(
            domain=domain,
            contains_personal_data=contains_personal_data,
            contains_sensitive_data=contains_health_data,
            contains_health_data=contains_health_data,
            contains_sensitive_health_data=contains_health_data,
            request_type=request_type,
            mentions_medication=mentions_medication,
            requires_professional_evaluation=contains_health_data and asks_for_permission,
            has_urgent_symptoms=has_urgent_symptoms,
            legal_basis_confirmed=False,
            purpose_confirmed=False,
            external_communication=False,
            requires_side_effect=False,
            fact_extraction_confidence=confidence,
            uncertainty_reasons=uncertainty_reasons,
            evidence=[term for term in HEALTH_TERMS + LEGAL_TERMS + FINANCE_TERMS + HR_TERMS if term in text][:10],
        )

        return facts, None
