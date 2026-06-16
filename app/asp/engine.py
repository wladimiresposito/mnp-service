from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

from app.asp.models import TemporalAspInput, TemporalAspResult


RULES_PATH = Path(__file__).resolve().parent.parent / "plugins" / "lgpd_temporal_asp" / "rules" / "base.lp"


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


class TemporalConsentEngine:
    """
    Experimental ASP/Clingo adapter.

    If clingo is installed, this engine evaluates the .lp rules. If clingo is
    absent, it uses a deterministic Python fallback with the same consent rule:
    consent holds when the latest relevant event before current_time is grant_consent.
    """

    def evaluate(self, asp_input: TemporalAspInput) -> TemporalAspResult:
        if clingo_available():
            return self._evaluate_with_clingo(asp_input)
        return self._evaluate_with_python_fallback(asp_input)

    def _evaluate_with_python_fallback(self, asp_input: TemporalAspInput) -> TemporalAspResult:
        relevant = [
            event for event in asp_input.events
            if event.subject == asp_input.subject
            and event.purpose == asp_input.purpose
            and event.t < asp_input.current_time
            and event.kind in {"grant_consent", "revoke_consent"}
        ]

        latest = max(relevant, key=lambda e: e.t) if relevant else None
        active_consent = bool(latest and latest.kind == "grant_consent")
        forbidden = bool(asp_input.sensitive_health_data and not active_consent)

        required_changes = []
        if forbidden:
            required_changes.extend([
                "obtain_active_consent",
                "confirm_purpose",
                "avoid_processing_sensitive_data_until_allowed",
            ])

        return TemporalAspResult(
            engine="python_fallback",
            clingo_available=False,
            allowed=not forbidden,
            active_consent=active_consent,
            forbidden=forbidden,
            required_changes=required_changes,
            answer_set=[],
            trace={
                "latest_relevant_event": latest.model_dump(mode="json") if latest else None,
                "events_considered": [event.model_dump(mode="json") for event in relevant],
                "rules_path": str(RULES_PATH),
            },
        )

    def _evaluate_with_clingo(self, asp_input: TemporalAspInput) -> TemporalAspResult:
        import clingo  # type: ignore

        subject = atomize(asp_input.subject)
        purpose = atomize(asp_input.purpose)
        current_time = max(int(asp_input.current_time), 0)

        program = []
        program.append(RULES_PATH.read_text(encoding="utf-8"))
        program.append(f"time(0..{current_time}).")
        program.append(f"subject({subject}).")
        program.append(f"purpose({purpose}).")
        program.append(f"current_time({current_time}).")
        program.append(f"candidate_process({subject},{purpose}).")

        if asp_input.sensitive_health_data:
            program.append(f"sensitive_health_data({subject}).")

        for event in asp_input.events:
            if event.kind not in {"grant_consent", "revoke_consent"}:
                continue
            ev_subject = atomize(event.subject)
            ev_purpose = atomize(event.purpose)
            program.append(f"happens({event.kind}({ev_subject},{ev_purpose}),{int(event.t)}).")

        ctl = clingo.Control(["--warn=none"])
        ctl.add("base", [], "\n".join(program))
        ctl.ground([("base", [])])

        symbols: list[str] = []

        with ctl.solve(yield_=True) as handle:
            for model in handle:
                symbols = sorted(str(symbol) for symbol in model.symbols(shown=True))
                break

        active_consent = f"holds_at(consent({subject},{purpose}),{current_time})" in symbols
        forbidden = any(symbol.startswith("forbidden(") for symbol in symbols)

        required_changes = []
        if any(symbol == "required_change(obtain_active_consent)" for symbol in symbols):
            required_changes.append("obtain_active_consent")
        if any(symbol == "required_change(confirm_purpose)" for symbol in symbols):
            required_changes.append("confirm_purpose")
        if any(symbol == "required_change(avoid_processing_sensitive_data_until_allowed)" for symbol in symbols):
            required_changes.append("avoid_processing_sensitive_data_until_allowed")

        return TemporalAspResult(
            engine="clingo",
            clingo_available=True,
            allowed=not forbidden,
            active_consent=active_consent,
            forbidden=forbidden,
            required_changes=required_changes,
            answer_set=symbols,
            trace={
                "subject_atom": subject,
                "purpose_atom": purpose,
                "rules_path": str(RULES_PATH),
                "program_facts": program[1:],
            },
        )


temporal_consent_engine = TemporalConsentEngine()
