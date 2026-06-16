#!/usr/bin/env python
"""Relatorio de divergencia em larga escala entre Clingo e fallback.

Diferente do teste (que e um gate em ~2500 casos), este script roda um
corpus grande sob demanda e reporta a taxa de divergencia por campo. Util
para inspecao manual apos mudar regras, e para gerar o numero auditavel
"N casos, 0 divergencias".

Uso:
    python scripts/divergence_report.py --n 20000 --seeds 1402 77 2024
"""
from __future__ import annotations

import argparse
from collections import Counter

from app.event_calculus.engine import ExplicitEventCalculusEngine, clingo_available
from app.testing.synthetic import generate_ec_corpus


def _fields(result) -> dict:
    consent = next((f for f in result.fluents if f.fluent.startswith("consent(")), None)
    d = result.decision
    return {
        "forbidden": d.forbidden,
        "allowed": d.allowed,
        "requires_escalation": d.requires_escalation,
        "risk_level": d.risk_level,
        "consent": consent.holds if consent else None,
        "violated_rules": tuple(sorted(d.violated_rules)),
        "required_changes": tuple(sorted(d.required_changes)),
        "consequences": tuple(sorted(c.consequence_id for c in d.consequences)),
        "obligations": tuple(sorted(o.obligation_id for o in d.obligations)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10000)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1402, 77, 2024])
    args = parser.parse_args()

    if not clingo_available():
        print("clingo nao instalado. Instale o extra [asp] para o relatorio.")
        return 2

    engine = ExplicitEventCalculusEngine()
    total = 0
    checked = 0
    by_field: Counter = Counter()

    for seed in args.seeds:
        for scenario in generate_ec_corpus(args.n, seed=seed):
            checked += 1
            a = _fields(engine._evaluate_with_clingo(scenario))
            b = _fields(engine._evaluate_with_python_fallback(scenario))
            if a != b:
                total += 1
                for key in a:
                    if a[key] != b[key]:
                        by_field[key] += 1

    print(f"Casos verificados : {checked}")
    print(f"Divergencias      : {total} ({100 * total / checked:.4f}%)")
    if by_field:
        print("Por campo:")
        for key, count in by_field.most_common():
            print(f"  {key}: {count}")
    else:
        print("Os dois motores sao equivalentes no contrato de decisao.")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
