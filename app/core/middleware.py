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

from app.core.composition import compose
from app.core.models import (
    ActionPlan,
    CompositionPolicy,
    Context,
    DraftAnswer,
    ToolCall,
    Verdict,
)
from app.core.module import NormativeModule


class NormativeMiddleware:
    def __init__(
        self,
        plugins: list[NormativeModule],
        composition: CompositionPolicy = CompositionPolicy.CONSERVATIVE,
    ) -> None:
        self.plugins = plugins
        self.composition = composition

    def _stamp(self, plugin: NormativeModule, verdict: Verdict) -> Verdict:
        """Carimba o flag binding do plugin no veredicto, para a composicao."""
        verdict.binding = plugin.metadata().binding
        return verdict

    def evaluate_input(self, context: Context) -> Verdict:
        return compose(
            [self._stamp(p, p.evaluate_input(context)) for p in self.plugins],
            self.composition, phase="input",
        )

    def evaluate_plan(self, plan: ActionPlan) -> Verdict:
        return compose(
            [self._stamp(p, p.evaluate_plan(plan)) for p in self.plugins],
            self.composition, phase="plan",
        )

    def evaluate_tool_call(self, tool_call: ToolCall) -> Verdict:
        return compose(
            [self._stamp(p, p.evaluate_tool_call(tool_call)) for p in self.plugins],
            self.composition, phase="tool_call",
        )

    def evaluate_output(self, draft: DraftAnswer) -> Verdict:
        return compose(
            [self._stamp(p, p.evaluate_output(draft)) for p in self.plugins],
            self.composition, phase="output",
        )

    def evaluate_all(
        self,
        context: Context | None = None,
        plan: ActionPlan | None = None,
        tool_call: ToolCall | None = None,
        draft: DraftAnswer | None = None,
    ) -> Verdict:
        verdicts: list[Verdict] = []
        if context is not None:
            verdicts.append(self.evaluate_input(context))
        if plan is not None:
            verdicts.append(self.evaluate_plan(plan))
        if tool_call is not None:
            verdicts.append(self.evaluate_tool_call(tool_call))
        if draft is not None:
            verdicts.append(self.evaluate_output(draft))
        # Os veredictos de fase ja sao compostos; aqui agregamos por fase.
        # Marca-os como vinculantes para nao rebaixar indevidamente.
        for v in verdicts:
            v.binding = True
        return compose(verdicts, self.composition, phase="all")
