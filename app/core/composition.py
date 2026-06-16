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

from app.core.models import CompositionPolicy, Decision, RiskLevel, Verdict

DECISION_PRIORITY = {
    Decision.ALLOW: 0,
    Decision.MODIFY: 1,
    Decision.ESCALATE: 2,
    Decision.BLOCK: 3,
}

RISK_PRIORITY = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


def _empty() -> Verdict:
    return Verdict(
        decision=Decision.ALLOW,
        risk_level=RiskLevel.LOW,
        explanation="Nenhum plugin ativo.",
        plugin_id="mnp_composite",
        plugin_version="1.0.0",
    )


def _aggregate(verdicts: list[Verdict], decision: Decision, risk: RiskLevel,
               phase: str, header: str) -> Verdict:
    violated_rules: set[str] = set()
    required_changes: set[str] = set()
    trace: list[dict] = []
    explanations: list[str] = []
    for verdict in verdicts:
        violated_rules.update(verdict.violated_rules)
        required_changes.update(verdict.required_changes)
        trace.append(verdict.model_dump(mode="json"))
        tag = "vinculante" if verdict.binding else "suplementar"
        explanations.append(f"[{verdict.plugin_id}/{tag}] {verdict.explanation}")
    return Verdict(
        decision=decision,
        risk_level=risk,
        violated_rules=sorted(violated_rules),
        required_changes=sorted(required_changes),
        explanation=f"{header} (fase '{phase}'). " + " ".join(explanations),
        trace=trace,
        plugin_id="mnp_composite",
        plugin_version="1.0.0",
    )


def compose_conservative(verdicts: list[Verdict], phase: str = "unknown") -> Verdict:
    """Composicao conservadora: decisao final = maior severidade entre todos.

    Adequada para alto risco. Nao distingue vinculante de suplementar, entao
    um plugin suplementar pode endurecer a decisao final.
    """
    if not verdicts:
        return _empty()
    final_decision = max((v.decision for v in verdicts), key=lambda d: DECISION_PRIORITY[d])
    final_risk = max((v.risk_level for v in verdicts), key=lambda r: RISK_PRIORITY[r])
    return _aggregate(verdicts, final_decision, final_risk, phase,
                      "Composicao conservadora")


def compose_hierarchical(verdicts: list[Verdict], phase: str = "unknown") -> Verdict:
    """Composicao hierarquica: normas vinculantes prevalecem.

    Regras:
      1. Se algum plugin vinculante restringe, sua decisao mais severa decide.
      2. Plugins suplementares (binding=False) nunca bloqueiam sozinhos: a
         restricao mais severa que levantam e rebaixada para escalonamento,
         honrando o alerta do artigo (Secao 4.3) de que obrigacao vinculante
         nao deve ser derrotada por plugin opinativo.
    """
    if not verdicts:
        return _empty()

    binding = [v for v in verdicts if v.binding]
    advisory = [v for v in verdicts if not v.binding]
    final_risk = max((v.risk_level for v in verdicts), key=lambda r: RISK_PRIORITY[r])

    if binding:
        worst_b = max((v.decision for v in binding), key=lambda d: DECISION_PRIORITY[d])
        if worst_b is not Decision.ALLOW:
            return _aggregate(verdicts, worst_b, final_risk, phase,
                              "Composicao hierarquica: norma vinculante prevalece")

    if advisory:
        worst_a = max((v.decision for v in advisory), key=lambda d: DECISION_PRIORITY[d])
        if worst_a is not Decision.ALLOW:
            decision = Decision.ESCALATE if worst_a is Decision.BLOCK else worst_a
            return _aggregate(
                verdicts, decision, final_risk, phase,
                "Composicao hierarquica: vinculantes permitem, suplementar "
                f"levantou '{worst_a.value}' aplicada como '{decision.value}'")

    return _aggregate(verdicts, Decision.ALLOW, final_risk, phase,
                      "Composicao hierarquica: sem restricoes")


_POLICIES = {
    CompositionPolicy.CONSERVATIVE: compose_conservative,
    CompositionPolicy.HIERARCHICAL: compose_hierarchical,
}


def compose(verdicts: list[Verdict],
            policy: CompositionPolicy = CompositionPolicy.CONSERVATIVE,
            phase: str = "unknown") -> Verdict:
    """Dispatcher de composicao por politica."""
    return _POLICIES.get(policy, compose_conservative)(verdicts, phase)
