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

from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_system import router as system_router
from app.api.routes_plugins import router as plugins_router
from app.api.routes_tenants import router as tenants_router
from app.api.routes_extract import router as extract_router
from app.api.routes_review import router as review_router
from app.api.routes_rag import router as rag_router
from app.api.routes_agent import router as agent_router
from app.api.routes_asp import router as asp_router
from app.api.routes_event_calculus import router as event_calculus_router
from app.api.routes_evaluate import router as evaluate_router
from app.api.routes_audit import router as audit_router
from app.api.routes_metrics import router as metrics_router
from app.audit.factory import init_audit_repository
from app.config.settings import settings
from app.security.middleware import install_release_middlewares


def create_app() -> FastAPI:
    init_audit_repository()

    app = FastAPI(
        title="MNP Service",
        description="Middleware Normativo Pluggable — Technical Release v1.0",
        version=settings.version,
    )

    install_release_middlewares(app)

    app.include_router(health_router)
    app.include_router(dashboard_router)
    app.include_router(system_router)
    app.include_router(plugins_router)
    app.include_router(tenants_router)
    app.include_router(extract_router)
    app.include_router(review_router)
    app.include_router(rag_router)
    app.include_router(agent_router)
    app.include_router(asp_router)
    app.include_router(event_calculus_router)
    app.include_router(evaluate_router)
    app.include_router(audit_router)
    app.include_router(metrics_router)

    return app


app = create_app()
