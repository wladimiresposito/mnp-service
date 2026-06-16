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


def version_info() -> dict:
    return {
        "service": settings.service_name,
        "version": settings.version,
        "release_name": settings.release_name,
        "env": settings.env,
        "audit_backend": settings.audit_backend,
        "default_fact_extractor": settings.default_fact_extractor,
    }
