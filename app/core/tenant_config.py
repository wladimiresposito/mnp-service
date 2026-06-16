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

from pathlib import Path
from typing import Any

import yaml

from app.core.models import CompositionPolicy, TenantPluginConfig


class TenantConfigError(ValueError):
    pass


class TenantConfigStore:
    def __init__(self, config_path: str) -> None:
        self.config_path = Path(config_path)
        self._configs: dict[str, TenantPluginConfig] = {}
        self.reload()

    def reload(self) -> None:
        if not self.config_path.exists():
            self._configs = {
                "default": TenantPluginConfig(
                    tenant_id="default",
                    composition=CompositionPolicy.CONSERVATIVE,
                    enabled_plugins=[],
                    disabled_plugins=[],
                    plugin_settings={},
                )
            }
            return

        raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        configs: dict[str, TenantPluginConfig] = {}

        for tenant_id, cfg in raw.items():
            if not isinstance(cfg, dict):
                raise TenantConfigError(f"Tenant config must be a mapping: {tenant_id}")

            configs[tenant_id] = TenantPluginConfig(
                tenant_id=tenant_id,
                composition=cfg.get("composition", "conservative"),
                enabled_plugins=list(cfg.get("enabled_plugins", [])),
                disabled_plugins=list(cfg.get("disabled_plugins", [])),
                plugin_settings=dict(cfg.get("plugin_settings", {})),
            )

        if "default" not in configs:
            configs["default"] = TenantPluginConfig(tenant_id="default")

        self._configs = configs

    def list_tenants(self) -> list[str]:
        return sorted(self._configs.keys())

    def get(self, tenant_id: str) -> TenantPluginConfig:
        return self._configs.get(tenant_id) or self._configs["default"]

    def raw(self) -> dict[str, Any]:
        return {tenant_id: cfg.model_dump(mode="json") for tenant_id, cfg in self._configs.items()}
