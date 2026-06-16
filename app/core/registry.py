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

from app.config.settings import settings
from app.core.models import PluginMetadata, TenantPluginConfig, TenantPluginView
from app.core.module import NormativeModule
from app.core.tenant_config import TenantConfigStore
from app.plugins.internal_policy_simplified.plugin import InternalPolicySimplifiedPlugin
from app.plugins.lgpd_br_simplified.plugin import LgpdBrSimplifiedPlugin
from app.plugins.lgpd_temporal_asp.plugin import LgpdTemporalAspPlugin
from app.plugins.lgpd_event_calculus.plugin import LgpdEventCalculusPlugin
from app.plugins.medical_safety_simplified.plugin import MedicalSafetySimplifiedPlugin


class PluginResolutionError(ValueError):
    pass


class PluginRegistry:
    def __init__(self, tenant_config_store: TenantConfigStore) -> None:
        self._plugins: dict[str, NormativeModule] = {}
        self.tenant_config_store = tenant_config_store

    def register(self, plugin: NormativeModule) -> None:
        meta = plugin.metadata()
        self._plugins[meta.plugin_id] = plugin

    def all_plugins(self) -> list[NormativeModule]:
        return list(self._plugins.values())

    def plugin_metadata(self) -> list[PluginMetadata]:
        return [plugin.metadata() for plugin in self.all_plugins()]

    def get_tenant_config(self, tenant_id: str) -> TenantPluginConfig:
        return self.tenant_config_store.get(tenant_id)

    def list_tenants(self) -> list[str]:
        return self.tenant_config_store.list_tenants()

    def reload_tenant_config(self) -> None:
        self.tenant_config_store.reload()

    def tenant_view(self, tenant_id: str) -> TenantPluginView:
        cfg = self.get_tenant_config(tenant_id)
        enabled_ids = self._effective_enabled_ids(cfg)
        enabled_meta = [self._plugins[pid].metadata() for pid in enabled_ids if pid in self._plugins]
        unknown = [pid for pid in enabled_ids if pid not in self._plugins]
        return TenantPluginView(
            tenant_id=cfg.tenant_id,
            composition=cfg.composition,
            enabled_plugins=enabled_meta,
            disabled_plugins=cfg.disabled_plugins,
            unknown_plugins=unknown,
            plugin_settings=cfg.plugin_settings,
        )

    def resolve_for_tenant(
        self,
        tenant_id: str,
        requested_plugin_ids: list[str] | None = None,
    ) -> tuple[list[NormativeModule], TenantPluginConfig, list[str]]:
        cfg = self.get_tenant_config(tenant_id)
        allowed_ids = self._effective_enabled_ids(cfg)

        if requested_plugin_ids is None:
            selected_ids = allowed_ids
        else:
            selected_ids = requested_plugin_ids

        unknown = [pid for pid in selected_ids if pid not in self._plugins]
        if unknown:
            raise PluginResolutionError(f"Unknown plugin(s): {', '.join(unknown)}")

        disabled = [pid for pid in selected_ids if pid in set(cfg.disabled_plugins)]
        if disabled:
            raise PluginResolutionError(
                f"Plugin(s) disabled for tenant '{cfg.tenant_id}': {', '.join(disabled)}"
            )

        not_allowed = [pid for pid in selected_ids if pid not in allowed_ids]
        if not_allowed:
            raise PluginResolutionError(
                f"Plugin(s) not enabled for tenant '{cfg.tenant_id}': {', '.join(not_allowed)}"
            )

        return [self._plugins[pid] for pid in selected_ids], cfg, selected_ids

    def _effective_enabled_ids(self, cfg: TenantPluginConfig) -> list[str]:
        disabled = set(cfg.disabled_plugins)
        return [pid for pid in cfg.enabled_plugins if pid not in disabled]


tenant_config_store = TenantConfigStore(settings.tenant_config_path)
default_registry = PluginRegistry(tenant_config_store)
default_registry.register(LgpdBrSimplifiedPlugin())
default_registry.register(LgpdTemporalAspPlugin())
default_registry.register(LgpdEventCalculusPlugin())
default_registry.register(MedicalSafetySimplifiedPlugin())
default_registry.register(InternalPolicySimplifiedPlugin())
