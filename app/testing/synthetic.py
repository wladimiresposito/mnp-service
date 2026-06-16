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

"""Gerador de casos sinteticos para teste diferencial e metamorfico.

Filosofia (resposta a "regras sinteticas melhoram a suficiencia?"):
  - Geramos CASOS, nao regras. Caso sintetico errado falha alto e e
    revisado; regra sintetica errada falha em silencio. Por isso casos
    sao seguros e regras exigem ratificacao humana.
  - O gerador e DETERMINISTICO dado um seed. Isso da um corpus de teste
    reproduzivel e versionavel, que e auditavel ("estes N casos passaram"),
    em vez de aleatoriedade nao reproduzivel.

Tres usos:
  1. Diferencial: roda cada caso nos dois motores (Clingo e fallback) e
     exige veredictos identicos. Teria pego a classe de bug do ASP cedo.
  2. Metamorfico: transformacoes que preservam (ou alteram de forma
     conhecida) o veredicto, checando propriedades sem saber a resposta
     exata.
  3. Propriedades de composicao: invariantes que nenhuma combinacao de
     plugins pode violar.
"""
from __future__ import annotations

import random

from app.event_calculus.models import ECEvent, ECScenario

CONSENT_KINDS = ("grant_consent", "revoke_consent")
OTHER_KINDS = ("change_purpose", "start_processing", "stop_processing",
               "data_breach", "human_review_approved", "human_review_rejected")
DATA_CATEGORIES = ("health", "personal", "sensitive", "general")
DEFAULT_PURPOSE = "process_health_data_for_pre_anamnesis"


def generate_ec_scenario(rng: random.Random, subject: str = "user-s") -> ECScenario:
    """Gera um ECScenario valido e variado a partir de um RNG semeado."""
    horizon = rng.randint(5, 30)
    current_time = rng.randint(2, horizon)
    n_events = rng.randint(0, 6)

    events: list[ECEvent] = []
    for _ in range(n_events):
        # Pesa eventos de consentimento, que sao o coracao do modelo.
        if rng.random() < 0.7:
            kind = rng.choice(CONSENT_KINDS)
        else:
            kind = rng.choice(OTHER_KINDS)
        t = rng.randint(1, horizon)
        events.append(ECEvent(t=t, kind=kind, subject=subject,
                              purpose=DEFAULT_PURPOSE))

    return ECScenario(
        subject=subject,
        purpose=DEFAULT_PURPOSE,
        current_time=current_time,
        data_category=rng.choice(DATA_CATEGORIES),
        events=events,
        requires_legal_basis=rng.random() < 0.85,
        requires_purpose_confirmation=rng.random() < 0.5,
        emergency_exception=rng.random() < 0.1,
        human_review_override=rng.random() < 0.1,
    )


def generate_ec_corpus(n: int, seed: int = 1402) -> list[ECScenario]:
    """Corpus reproduzivel de n cenarios. Mesmo seed, mesmo corpus."""
    rng = random.Random(seed)
    return [generate_ec_scenario(rng, subject=f"user-{i}") for i in range(n)]


# ---------------------------------------------------------------------------
# Transformacoes metamorficas: alteram o cenario de modo que a relacao com o
# veredicto original e conhecida, mesmo sem saber o veredicto exato.
# ---------------------------------------------------------------------------

def add_future_event(scenario: ECScenario, rng: random.Random) -> ECScenario:
    """Adiciona um evento APOS current_time.

    Propriedade: eventos no futuro nao podem afetar o veredicto presente
    (o Event Calculus so considera happens(E,T0) com T0 < current_time).
    O veredicto deve permanecer identico.
    """
    future_t = scenario.current_time + rng.randint(1, 5)
    kind = rng.choice(CONSENT_KINDS + OTHER_KINDS)
    new_events = list(scenario.events) + [
        ECEvent(t=future_t, kind=kind, subject=scenario.subject,
                purpose=scenario.purpose)
    ]
    return scenario.model_copy(update={"events": new_events})


def drop_legal_basis_requirement(scenario: ECScenario) -> ECScenario:
    """Remove a exigencia de base legal.

    Propriedade: sem exigencia de base legal, o cenario nunca pode ficar
    MAIS restritivo. Se antes era permitido, continua permitido.
    """
    return scenario.model_copy(update={"requires_legal_basis": False,
                                       "requires_purpose_confirmation": False})


def add_emergency_exception(scenario: ECScenario) -> ECScenario:
    """Ativa excecao de emergencia.

    Propriedade: a excecao so pode relaxar, nunca endurecer. Um cenario
    antes permitido nao pode virar proibido por causa dela.
    """
    return scenario.model_copy(update={"emergency_exception": True})
