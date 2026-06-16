from app.core.composition import compose_conservative, compose_hierarchical
from app.core.models import Decision, RiskLevel, Verdict


def _v(plugin_id, decision, binding, risk=RiskLevel.MEDIUM):
    return Verdict(
        decision=decision, risk_level=risk, plugin_id=plugin_id,
        plugin_version="t", explanation="x", binding=binding,
    )


def test_hierarchical_supplementary_block_is_downgraded_to_escalate():
    # Norma vinculante permite; plugin suplementar quer bloquear.
    # Hierarquica nao deixa o suplementar bloquear sozinho: rebaixa para escalate.
    verdicts = [
        _v("lgpd_br_simplified", Decision.ALLOW, binding=True),
        _v("internal_policy_simplified", Decision.BLOCK, binding=False),
    ]
    out = compose_hierarchical(verdicts, phase="output")
    assert out.decision is Decision.ESCALATE


def test_hierarchical_binding_block_prevails():
    verdicts = [
        _v("lgpd_br_simplified", Decision.BLOCK, binding=True),
        _v("internal_policy_simplified", Decision.ALLOW, binding=False),
    ]
    out = compose_hierarchical(verdicts, phase="output")
    assert out.decision is Decision.BLOCK


def test_hierarchical_supplementary_modify_is_kept():
    verdicts = [
        _v("lgpd_br_simplified", Decision.ALLOW, binding=True),
        _v("internal_policy_simplified", Decision.MODIFY, binding=False),
    ]
    out = compose_hierarchical(verdicts, phase="output")
    assert out.decision is Decision.MODIFY


def test_conservative_supplementary_block_still_blocks():
    # Contraste: na conservadora, o suplementar endurece a decisao.
    verdicts = [
        _v("lgpd_br_simplified", Decision.ALLOW, binding=True),
        _v("internal_policy_simplified", Decision.BLOCK, binding=False),
    ]
    out = compose_conservative(verdicts, phase="output")
    assert out.decision is Decision.BLOCK


def test_hierarchical_all_allow():
    verdicts = [
        _v("a", Decision.ALLOW, binding=True),
        _v("b", Decision.ALLOW, binding=False),
    ]
    out = compose_hierarchical(verdicts, phase="output")
    assert out.decision is Decision.ALLOW
