"""Cross-validacao entre o motor Clingo e o fallback Python (item 1).

Este e o teste de maior retorno da revisao. A suite original passava 40/40
apenas porque o Clingo NAO estava instalado: tudo rodava pelo fallback. O
caminho simbolico real nunca era exercitado, e os dois caminhos podiam
divergir em silencio. Aqui forcamos os dois motores a resolverem os mesmos
cenarios e exigimos resultados identicos nos campos que importam.

Se o Clingo nao estiver instalado, o teste e pulado (skip), mas o CI deve
instalar o extra [asp] para que ele rode de fato (ver .github/workflows).
"""
import pytest

from app.event_calculus.engine import ExplicitEventCalculusEngine, clingo_available
from app.event_calculus.models import ECEvent, ECScenario
from app.asp.engine import TemporalConsentEngine
from app.asp.models import TemporalAspInput, TemporalEvent

pytestmark = pytest.mark.skipif(
    not clingo_available(),
    reason="clingo nao instalado; instale o extra [asp] para a cross-validacao",
)


def _ec_summary(result):
    consent = next(f for f in result.fluents if f.fluent.startswith("consent("))
    return {
        "forbidden": result.decision.forbidden,
        "consent_holds": consent.holds,
        "violated_rules": sorted(result.decision.violated_rules),
        "required_changes": sorted(result.decision.required_changes),
    }


EC_SCENARIOS = {
    "active_consent": ECScenario(
        subject="user-1", purpose="p", current_time=10, data_category="health",
        requires_legal_basis=True, requires_purpose_confirmation=False,
        events=[ECEvent(t=1, kind="grant_consent", subject="user-1", purpose="p")],
    ),
    "revoked_consent": ECScenario(
        subject="user-1", purpose="p", current_time=10, data_category="health",
        requires_legal_basis=True, requires_purpose_confirmation=False,
        events=[
            ECEvent(t=1, kind="grant_consent", subject="user-1", purpose="p"),
            ECEvent(t=5, kind="revoke_consent", subject="user-1", purpose="p"),
        ],
    ),
    "never_consented": ECScenario(
        subject="user-1", purpose="p", current_time=10, data_category="health",
        requires_legal_basis=True, requires_purpose_confirmation=False,
        events=[],
    ),
}


@pytest.mark.parametrize("name", list(EC_SCENARIOS))
def test_event_calculus_clingo_matches_python_fallback(name):
    engine = ExplicitEventCalculusEngine()
    scenario = EC_SCENARIOS[name]
    clingo_res = engine._evaluate_with_clingo(scenario)
    python_res = engine._evaluate_with_python_fallback(scenario)
    assert _ec_summary(clingo_res) == _ec_summary(python_res), (
        f"Divergencia no cenario '{name}':\n"
        f"clingo  = {_ec_summary(clingo_res)}\n"
        f"fallback= {_ec_summary(python_res)}"
    )


ASP_SCENARIOS = {
    "active": TemporalAspInput(
        subject="user-1", purpose="p", current_time=10, sensitive_health_data=True,
        events=[TemporalEvent(t=1, kind="grant_consent", subject="user-1", purpose="p")],
    ),
    "revoked": TemporalAspInput(
        subject="user-1", purpose="p", current_time=10, sensitive_health_data=True,
        events=[
            TemporalEvent(t=1, kind="grant_consent", subject="user-1", purpose="p"),
            TemporalEvent(t=5, kind="revoke_consent", subject="user-1", purpose="p"),
        ],
    ),
    "none": TemporalAspInput(
        subject="user-1", purpose="p", current_time=10, sensitive_health_data=True,
        events=[],
    ),
}


def _asp_summary(r):
    return {
        "allowed": r.allowed,
        "active_consent": r.active_consent,
        "forbidden": r.forbidden,
        "required_changes": sorted(r.required_changes),
    }


@pytest.mark.parametrize("name", list(ASP_SCENARIOS))
def test_temporal_asp_clingo_matches_python_fallback(name):
    engine = TemporalConsentEngine()
    scenario = ASP_SCENARIOS[name]
    clingo_res = engine._evaluate_with_clingo(scenario)
    python_res = engine._evaluate_with_python_fallback(scenario)
    assert _asp_summary(clingo_res) == _asp_summary(python_res), (
        f"Divergencia ASP no cenario '{name}':\n"
        f"clingo  = {_asp_summary(clingo_res)}\n"
        f"fallback= {_asp_summary(python_res)}"
    )
