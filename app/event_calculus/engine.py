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

import importlib.util
import re
from pathlib import Path

from app.event_calculus.models import (
    ECConsequence,
    ECDecision,
    ECEvent,
    ECFluentState,
    ECObligation,
    ECResult,
    ECScenario,
)


RULES_DIR = Path(__file__).resolve().parent.parent / "plugins" / "lgpd_event_calculus" / "rules"


def clingo_available() -> bool:
    return importlib.util.find_spec("clingo") is not None


def atomize(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = "unknown"
    if value[0].isdigit():
        value = "x_" + value
    return value


class ExplicitEventCalculusEngine:
    """
    Explicit Event Calculus-style evaluator.

    It exposes the concepts that were implicit in v0.7:
    - events
    - fluents
    - initiates
    - terminates
    - clipped
    - obligations
    - exceptions
    - consequences

    If Clingo is installed, it evaluates the ASP modules. Without Clingo,
    it uses a deterministic Python fallback mirroring the same demo semantics.
    """

    def evaluate(self, scenario: ECScenario) -> ECResult:
        if clingo_available():
            return self._evaluate_with_clingo(scenario)
        return self._evaluate_with_python_fallback(scenario)

    def _latest_event(
        self,
        scenario: ECScenario,
        kinds: set[str],
        purpose: str | None = None,
        before_t: int | None = None,
    ) -> ECEvent | None:
        before_t = scenario.current_time if before_t is None else before_t
        relevant = [
            event for event in scenario.events
            if event.kind in kinds
            and event.subject == scenario.subject
            and event.t < before_t
            and (purpose is None or event.purpose == purpose)
        ]
        return max(relevant, key=lambda e: e.t) if relevant else None

    def _events_between(
        self,
        scenario: ECScenario,
        kinds: set[str],
        start_t: int,
        end_t: int,
        purpose: str | None = None,
    ) -> list[ECEvent]:
        return [
            event for event in scenario.events
            if event.kind in kinds
            and event.subject == scenario.subject
            and start_t < event.t < end_t
            and (purpose is None or event.purpose == purpose)
        ]

    def _fluent_consent(self, scenario: ECScenario) -> ECFluentState:
        grant = self._latest_event(scenario, {"grant_consent"}, purpose=scenario.purpose)
        clipped_by: list[ECEvent] = []
        terminated_by = None

        if grant:
            clipped_by = self._events_between(
                scenario,
                {"revoke_consent", "change_purpose"},
                start_t=grant.t,
                end_t=scenario.current_time,
                purpose=scenario.purpose,
            )
            terminated_by = max(clipped_by, key=lambda e: e.t) if clipped_by else None

        holds = bool(grant and not clipped_by)
        return ECFluentState(
            fluent=f"consent({scenario.subject},{scenario.purpose})",
            holds=holds,
            initiated_by=grant,
            terminated_by=terminated_by,
            clipped_by=clipped_by,
        )

    def _fluent_purpose_confirmed(self, scenario: ECScenario) -> ECFluentState:
        if not scenario.requires_purpose_confirmation:
            return ECFluentState(
                fluent=f"purpose_confirmed({scenario.subject},{scenario.purpose})",
                holds=True,
            )

        # Espelha o Clingo (20_lgpd_fluents.lp): grant_consent INICIA
        # purpose_confirmed e apenas change_purpose o TERMINA. Diferente do
        # consent, revoke_consent NAO termina purpose_confirmed. O calculo
        # tem de seguir essa regra, e nao colar em consent.holds (bug pego
        # pelo teste diferencial sintetico: grant seguido de revoke deixava
        # purpose_confirmed falso no fallback e verdadeiro no Clingo).
        grant = self._latest_event(scenario, {"grant_consent"}, purpose=scenario.purpose)
        clipped_by: list[ECEvent] = []
        terminated_by = None
        if grant:
            clipped_by = self._events_between(
                scenario,
                {"change_purpose"},
                start_t=grant.t,
                end_t=scenario.current_time,
                purpose=scenario.purpose,
            )
            terminated_by = max(clipped_by, key=lambda e: e.t) if clipped_by else None
        holds = bool(grant and not clipped_by)
        return ECFluentState(
            fluent=f"purpose_confirmed({scenario.subject},{scenario.purpose})",
            holds=holds,
            initiated_by=grant,
            terminated_by=terminated_by,
            clipped_by=clipped_by,
        )

    def _fluent_processing_active(self, scenario: ECScenario) -> ECFluentState:
        start = self._latest_event(scenario, {"start_processing"}, purpose=scenario.purpose)
        clipped_by: list[ECEvent] = []
        terminated_by = None

        if start:
            clipped_by = self._events_between(
                scenario,
                {"stop_processing"},
                start_t=start.t,
                end_t=scenario.current_time,
                purpose=scenario.purpose,
            )
            terminated_by = max(clipped_by, key=lambda e: e.t) if clipped_by else None

        holds = bool(start and not clipped_by)
        return ECFluentState(
            fluent=f"processing_active({scenario.subject},{scenario.purpose})",
            holds=holds,
            initiated_by=start,
            terminated_by=terminated_by,
            clipped_by=clipped_by,
        )

    def _evaluate_with_python_fallback(self, scenario: ECScenario) -> ECResult:
        consent = self._fluent_consent(scenario)
        purpose_confirmed = self._fluent_purpose_confirmed(scenario)
        processing_active = self._fluent_processing_active(scenario)

        fluents = [consent, purpose_confirmed, processing_active]

        emergency_exception = scenario.emergency_exception
        # Espelha o Clingo: o override vem apenas da flag human_review_override.
        # Os eventos human_review_approved/rejected NAO concedem override hoje;
        # mante-los como override exigiria modela-los como fluente no ASP
        # (approved inicia, rejected termina), que e uma DECISAO NORMATIVA
        # pendente de ratificacao, nao um detalhe de implementacao. Ate la,
        # os dois motores tratam esses eventos como inertes, de forma
        # consistente. Ver docs/SYNTHETIC_TESTING.md (questoes em aberto).
        human_override = scenario.human_review_override

        # Breach conta se ocorreu ATE current_time (inclusive do "agora"),
        # nunca no futuro. Convencao alinhada com o Clingo (guarda T0 <= CT).
        has_breach = any(
            e.kind == "data_breach" and e.t <= scenario.current_time
            for e in scenario.events
        )

        forbidden = False
        violated_rules: list[str] = []
        required_changes: list[str] = []
        obligations: list[ECObligation] = []
        consequences: list[ECConsequence] = []

        # Reconciliacao com o motor Clingo (descoberta via teste diferencial
        # sintetico): no ASP, ambas as proibicoes passam por
        # sensitive_processing_candidate, isto e, so se aplicam a dados
        # sensiveis (health/sensitive). E avoid_processing e emitido para
        # QUALQUER proibicao. O fallback agora espelha isso exatamente.
        is_sensitive_candidate = scenario.data_category in {"health", "sensitive"}
        gate_open = not emergency_exception and not human_override

        forbidden_no_consent = (
            is_sensitive_candidate
            and scenario.requires_legal_basis
            and not consent.holds
            and gate_open
        )
        forbidden_no_purpose = (
            is_sensitive_candidate
            and scenario.requires_purpose_confirmation
            and not purpose_confirmed.holds
            and gate_open
        )

        if forbidden_no_consent:
            forbidden = True
            violated_rules.append("ec_sensitive_processing_without_active_consent")
            required_changes.append("obtain_active_consent")
            obligations.append(
                ECObligation(
                    obligation_id="obl_obtain_active_consent",
                    description="Obter ou confirmar base/consentimento ativo antes do tratamento.",
                    due_time=scenario.current_time,
                    triggered_by="ec_sensitive_processing_without_active_consent",
                    satisfied=False,
                )
            )

        if forbidden_no_purpose:
            forbidden = True
            if "ec_purpose_not_confirmed" not in violated_rules:
                violated_rules.append("ec_purpose_not_confirmed")
            if "confirm_purpose" not in required_changes:
                required_changes.append("confirm_purpose")
            # Espelha o Clingo: obligation(obl_confirm_purpose) deriva da
            # violacao de proposito (faltava no fallback).
            obligations.append(
                ECObligation(
                    obligation_id="obl_confirm_purpose",
                    description="Confirmar a finalidade do tratamento antes de prosseguir.",
                    due_time=scenario.current_time,
                    triggered_by="ec_purpose_not_confirmed",
                    satisfied=False,
                )
            )

        # avoid_processing: emitido uma vez para qualquer proibicao (espelha
        # required_change(avoid_processing...) :- forbidden(...) do Clingo).
        if forbidden:
            required_changes.append("avoid_processing_sensitive_data_until_allowed")

        if has_breach:
            obligations.append(
                ECObligation(
                    obligation_id="obl_log_and_notify_breach",
                    description="Registrar incidente e acionar processo de avaliação/notificação de violação.",
                    due_time=scenario.current_time + 1,
                    triggered_by="data_breach",
                    satisfied=False,
                )
            )
            consequences.append(
                ECConsequence(
                    consequence_id="cons_breach_response_required",
                    severity="critical",
                    description="Incidente de dados exige resposta operacional e possivelmente comunicação.",
                    triggered_by="data_breach",
                )
            )

        if forbidden:
            consequences.append(
                ECConsequence(
                    consequence_id="cons_processing_must_be_modified_or_stopped",
                    severity="high",
                    description="Tratamento de dado sensível deve ser modificado, interrompido ou escalado.",
                    triggered_by="forbidden_processing",
                )
            )

        requires_escalation = bool(
            has_breach
            or (forbidden and not human_override and not emergency_exception)
        )
        risk_level = "critical" if has_breach else ("high" if forbidden else "low")

        decision = ECDecision(
            allowed=not forbidden,
            forbidden=forbidden,
            requires_escalation=requires_escalation,
            risk_level=risk_level,
            violated_rules=violated_rules,
            required_changes=sorted(set(required_changes)),
            obligations=obligations,
            consequences=consequences,
        )

        return ECResult(
            engine="python_event_calculus_fallback",
            clingo_available=False,
            scenario=scenario,
            fluents=fluents,
            decision=decision,
            answer_set=[],
            trace={
                "emergency_exception": emergency_exception,
                "human_review_override": human_override,
                "rules_dir": str(RULES_DIR),
                "events": [event.model_dump(mode="json") for event in scenario.events],
            },
        )

    def _evaluate_with_clingo(self, scenario: ECScenario) -> ECResult:
        import clingo  # type: ignore

        subject = atomize(scenario.subject)
        purpose = atomize(scenario.purpose)
        data_category = atomize(scenario.data_category)
        current_time = int(scenario.current_time)

        modules = [
            "00_domain.lp",
            "10_event_calculus.lp",
            "20_lgpd_fluents.lp",
            "30_obligations.lp",
            "40_exceptions.lp",
            "50_consequences.lp",
        ]

        program_parts: list[str] = []
        for module in modules:
            program_parts.append((RULES_DIR / module).read_text(encoding="utf-8"))

        program_parts.append(f"time(0..{current_time}).")
        program_parts.append(f"subject({subject}).")
        program_parts.append(f"purpose({purpose}).")
        program_parts.append(f"data_category({subject},{data_category}).")
        program_parts.append(f"current_time({current_time}).")
        program_parts.append(f"candidate_process({subject},{purpose}).")

        if scenario.requires_legal_basis:
            program_parts.append("requires_legal_basis.")
        if scenario.requires_purpose_confirmation:
            program_parts.append("requires_purpose_confirmation.")
        if scenario.emergency_exception:
            program_parts.append(f"emergency_exception({subject},{purpose}).")
        if scenario.human_review_override:
            program_parts.append(f"human_review_override({subject},{purpose}).")

        for event in scenario.events:
            ev_subject = atomize(event.subject)
            ev_purpose = atomize(event.purpose)
            ev_kind = atomize(event.kind)
            program_parts.append(f"happens({ev_kind}({ev_subject},{ev_purpose}),{int(event.t)}).")

        ctl = clingo.Control(["--warn=none"])
        ctl.add("base", [], "\n".join(program_parts))
        ctl.ground([("base", [])])

        symbols: list[str] = []
        with ctl.solve(yield_=True) as handle:
            for model in handle:
                symbols = sorted(str(symbol) for symbol in model.symbols(shown=True))
                break

        def has(prefix: str) -> bool:
            return any(symbol.startswith(prefix) for symbol in symbols)

        # FIX: o estado do fluente deve ser consultado em current_time,
        # nao "em algum instante". Sem isso, um consentimento ja revogado
        # aparece como vigente na trilha, contradizendo a decisao.
        ct = current_time
        consent_holds = f"holds_at(consent({subject},{purpose}),{ct})" in symbols
        purpose_holds = f"holds_at(purpose_confirmed({subject},{purpose}),{ct})" in symbols
        processing_holds = f"holds_at(processing_active({subject},{purpose}),{ct})" in symbols

        # Proveniencia: eventos que iniciaram/interromperam o consentimento
        # ate current_time, para a trilha de auditoria.
        consent_inits = [e for e in scenario.events
                         if e.kind == "grant_consent" and e.t < ct]
        consent_clips = [e for e in scenario.events
                         if e.kind in ("revoke_consent", "change_purpose") and e.t < ct]
        fluents = [
            ECFluentState(
                fluent=f"consent({scenario.subject},{scenario.purpose})",
                holds=consent_holds,
                initiated_by=consent_inits[-1] if consent_inits else None,
                clipped_by=consent_clips,
            ),
            ECFluentState(fluent=f"purpose_confirmed({scenario.subject},{scenario.purpose})", holds=purpose_holds),
            ECFluentState(fluent=f"processing_active({scenario.subject},{scenario.purpose})", holds=processing_holds),
        ]

        forbidden = has("forbidden(")
        requires_escalation = has("requires_escalation(")

        violated_rules = [
            _extract_arg(symbol)
            for symbol in symbols
            if symbol.startswith("violated_rule(")
        ]

        required_changes = [
            _extract_arg(symbol)
            for symbol in symbols
            if symbol.startswith("required_change(")
        ]

        obligations = [
            ECObligation(
                obligation_id=_extract_arg(symbol),
                description=_extract_arg(symbol),
                triggered_by="asp_obligation",
                satisfied=False,
            )
            for symbol in symbols
            if symbol.startswith("obligation(")
        ]

        consequences = [
            ECConsequence(
                consequence_id="cons_" + _extract_arg(symbol),
                severity="high",
                description=_extract_arg(symbol),
                triggered_by="asp_consequence",
            )
            for symbol in symbols
            if symbol.startswith("consequence(")
        ]

        risk_level = "critical" if "consequence(breach_response_required)" in symbols else ("high" if forbidden else "low")

        return ECResult(
            engine="clingo_event_calculus",
            clingo_available=True,
            scenario=scenario,
            fluents=fluents,
            decision=ECDecision(
                allowed=not forbidden,
                forbidden=forbidden,
                requires_escalation=requires_escalation,
                risk_level=risk_level,
                violated_rules=violated_rules,
                required_changes=sorted(set(required_changes)),
                obligations=obligations,
                consequences=consequences,
            ),
            answer_set=symbols,
            trace={
                "rules_dir": str(RULES_DIR),
                "modules": modules,
                "program_facts": program_parts[len(modules):],
            },
        )


def _extract_arg(symbol: str) -> str:
    start = symbol.find("(")
    end = symbol.rfind(")")
    if start < 0 or end <= start:
        return symbol
    return symbol[start + 1:end]


event_calculus_engine = ExplicitEventCalculusEngine()
