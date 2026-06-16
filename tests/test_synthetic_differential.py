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

"""Teste diferencial e metamorfico sobre casos sinteticos (resposta a
"regras sinteticas melhoram a suficiencia?").

Casos sinteticos, nao regras sinteticas: o gerador produz CENARIOS e os
dois motores (Clingo e fallback) tem de concordar. Erro de caso falha
alto e e revisado; e o oposto de uma regra sintetica errada, que falharia
em silencio. Este teste ja pagou seu custo: encontrou ~30% de divergencia
entre os motores num caminho que os testes escritos a mao nao cobriam, e
guiou a reconciliacao ate 0/35000.
"""
import random

import pytest

from app.event_calculus.engine import ExplicitEventCalculusEngine, clingo_available
from app.testing.synthetic import (add_emergency_exception, add_future_event,
                                    drop_legal_basis_requirement,
                                    generate_ec_corpus, generate_ec_scenario)

pytestmark = pytest.mark.skipif(
    not clingo_available(),
    reason="clingo nao instalado; instale o extra [asp] para o teste diferencial",
)

ENGINE = ExplicitEventCalculusEngine()


def _decision(result):
    """Contrato diferencial: a DECISAO e os fluentes relevantes a ela.

    Estado de fluente irrelevante a decisao (ex.: purpose_confirmed quando
    nao exigido) nao faz parte do contrato e nao e comparado.
    """
    consent = next((f for f in result.fluents if f.fluent.startswith("consent(")), None)
    d = result.decision
    return (
        d.forbidden, d.allowed, d.requires_escalation, d.risk_level,
        consent.holds if consent else None,
        tuple(sorted(d.violated_rules)),
        tuple(sorted(d.required_changes)),
        tuple(sorted(c.consequence_id for c in d.consequences)),
        tuple(sorted(o.obligation_id for o in d.obligations)),
    )


@pytest.mark.parametrize("seed", [1402, 77, 2024, 999, 5])
def test_differential_clingo_equals_fallback_on_synthetic_corpus(seed):
    """Os dois motores produzem a mesma decisao em todo o corpus."""
    corpus = generate_ec_corpus(500, seed=seed)
    mismatches = []
    for i, scenario in enumerate(corpus):
        clingo_res = ENGINE._evaluate_with_clingo(scenario)
        python_res = ENGINE._evaluate_with_python_fallback(scenario)
        if _decision(clingo_res) != _decision(python_res):
            mismatches.append(i)
    assert not mismatches, (
        f"{len(mismatches)} divergencias clingo/fallback no seed {seed}: "
        f"primeiros indices {mismatches[:5]}"
    )


# ---------------------------------------------------------------------------
# Metamorficos: propriedades que valem sem saber o veredicto exato. Rodam em
# ambos os motores.
# ---------------------------------------------------------------------------

def _both_engines(scenario):
    return ENGINE._evaluate_with_clingo(scenario), ENGINE._evaluate_with_python_fallback(scenario)


@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55])
def test_metamorphic_future_event_does_not_change_decision(seed):
    """Evento apos current_time nao pode alterar a decisao presente."""
    rng = random.Random(seed)
    base = generate_ec_scenario(rng, subject="user-m")
    mutated = add_future_event(base, rng)
    for engine_name, evaluate in (("clingo", ENGINE._evaluate_with_clingo),
                                  ("fallback", ENGINE._evaluate_with_python_fallback)):
        before = _decision(evaluate(base))
        after = _decision(evaluate(mutated))
        assert before == after, (
            f"[{engine_name}] evento futuro mudou a decisao no seed {seed}")


@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55, 66, 77, 88])
def test_metamorphic_dropping_legal_basis_never_more_restrictive(seed):
    """Remover a exigencia de base legal nunca pode endurecer a decisao.

    Se antes era permitido, continua permitido (monotonicidade).
    """
    rng = random.Random(seed)
    base = generate_ec_scenario(rng, subject="user-m")
    relaxed = drop_legal_basis_requirement(base)
    for evaluate in (ENGINE._evaluate_with_clingo, ENGINE._evaluate_with_python_fallback):
        base_allowed = evaluate(base).decision.allowed
        relaxed_allowed = evaluate(relaxed).decision.allowed
        if base_allowed:
            assert relaxed_allowed, f"relaxar base legal proibiu o que era permitido (seed {seed})"


@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55, 66])
def test_metamorphic_emergency_exception_only_relaxes(seed):
    """Excecao de emergencia so pode relaxar, nunca endurecer."""
    rng = random.Random(seed)
    base = generate_ec_scenario(rng, subject="user-m")
    with_emergency = add_emergency_exception(base)
    for evaluate in (ENGINE._evaluate_with_clingo, ENGINE._evaluate_with_python_fallback):
        if evaluate(base).decision.allowed:
            assert evaluate(with_emergency).decision.allowed, (
                f"emergencia tornou proibido o que era permitido (seed {seed})")


def test_corpus_is_reproducible():
    """Mesmo seed, mesmo corpus: requisito para auditoria do conjunto de teste."""
    a = generate_ec_corpus(50, seed=2024)
    b = generate_ec_corpus(50, seed=2024)
    assert [s.model_dump() for s in a] == [s.model_dump() for s in b]
