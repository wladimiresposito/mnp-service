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

import sys
from pathlib import Path
from typing import Any

import yaml

from app.core.middleware import NormativeMiddleware
from app.core.models import Context, DraftAnswer, ActionPlan, ToolCall
from app.core.registry import default_registry


class NormativeTestFailure(AssertionError):
    pass


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("Normative test file must contain a list of cases.")
    return data


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    tenant_id = case.get("tenant_id", "default")
    plugin_ids = case.get("plugins")
    plugins, cfg, active_ids = default_registry.resolve_for_tenant(tenant_id, plugin_ids)
    mnp = NormativeMiddleware(plugins, composition=cfg.composition)

    input_data = case.get("input", {})

    context = None
    if "context" in input_data:
        context = Context(**input_data["context"])

    plan = None
    if "plan" in input_data:
        plan = ActionPlan(**input_data["plan"])

    tool_call = None
    if "tool_call" in input_data:
        tool_call = ToolCall(**input_data["tool_call"])

    draft = None
    if "draft" in input_data:
        draft = DraftAnswer(**input_data["draft"])

    verdict = mnp.evaluate_all(
        context=context,
        plan=plan,
        tool_call=tool_call,
        draft=draft,
    )

    expected = case.get("expected", {})
    expected_decision = expected.get("decision")
    expected_risk = expected.get("risk_level")
    required_rules = expected.get("required_rules", [])
    required_changes = expected.get("required_changes", [])

    errors = []

    if expected_decision and verdict.decision.value != expected_decision:
        errors.append(f"decision expected={expected_decision} actual={verdict.decision.value}")

    if expected_risk and verdict.risk_level.value != expected_risk:
        errors.append(f"risk_level expected={expected_risk} actual={verdict.risk_level.value}")

    for rule in required_rules:
        if rule not in verdict.violated_rules:
            errors.append(f"missing rule: {rule}")

    for change in required_changes:
        if change not in verdict.required_changes:
            errors.append(f"missing required_change: {change}")

    result = {
        "name": case.get("name", "<unnamed>"),
        "tenant_id": cfg.tenant_id,
        "active_plugins": active_ids,
        "passed": not errors,
        "errors": errors,
        "verdict": verdict.model_dump(mode="json"),
    }

    return result


def run_cases(path: str | Path) -> list[dict[str, Any]]:
    return [run_case(case) for case in load_cases(path)]


def assert_cases(path: str | Path) -> list[dict[str, Any]]:
    results = run_cases(path)
    failures = [result for result in results if not result["passed"]]
    if failures:
        message = "\n".join(
            f"- {f['name']}: {', '.join(f['errors'])}"
            for f in failures
        )
        raise NormativeTestFailure(f"Normative test failures:\n{message}")
    return results


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "normative_tests/cases.yaml"
    results = run_cases(path)
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {result['name']} -> {result['verdict']['decision']} / {result['verdict']['risk_level']}")
        for error in result["errors"]:
            print(f"  - {error}")
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
