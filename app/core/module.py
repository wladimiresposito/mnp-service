from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.models import (
    ActionPlan,
    Context,
    DraftAnswer,
    PluginMetadata,
    ToolCall,
    Verdict,
)


class NormativeModule(ABC):
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        raise NotImplementedError

    def evaluate_input(self, context: Context) -> Verdict:
        meta = self.metadata()
        return Verdict.allow(meta.plugin_id, meta.plugin_version)

    def evaluate_plan(self, plan: ActionPlan) -> Verdict:
        meta = self.metadata()
        return Verdict.allow(meta.plugin_id, meta.plugin_version)

    def evaluate_tool_call(self, tool_call: ToolCall) -> Verdict:
        meta = self.metadata()
        return Verdict.allow(meta.plugin_id, meta.plugin_version)

    def evaluate_output(self, draft: DraftAnswer) -> Verdict:
        meta = self.metadata()
        return Verdict.allow(meta.plugin_id, meta.plugin_version)
