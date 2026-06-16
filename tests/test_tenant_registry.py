from fastapi.testclient import TestClient

from app.main import app
from app.core.registry import default_registry

client = TestClient(app)


def test_tenant_plugins_endpoint():
    response = client.get("/tenants/clinic-demo/plugins")
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == "clinic-demo"
    enabled = {plugin["plugin_id"] for plugin in body["enabled_plugins"]}
    assert "lgpd_br_simplified" in enabled
    assert "medical_safety_simplified" in enabled
    assert "internal_policy_simplified" in enabled


def test_legal_demo_disables_medical_plugin():
    view = default_registry.tenant_view("legal-demo")
    enabled = {plugin.plugin_id for plugin in view.enabled_plugins}
    assert "medical_safety_simplified" not in enabled
    assert "medical_safety_simplified" in view.disabled_plugins


def test_requesting_disabled_plugin_returns_400():
    payload = {
        "tenant_id": "legal-demo",
        "draft": {
            "text": "Pode usar a pomada com corticoide.",
            "facts": {
                "domain": "healthcare",
                "request_type": "clinical_recommendation",
                "mentions_medication": True
            },
            "confidence": 0.82
        },
        "plugins": ["medical_safety_simplified"]
    }

    response = client.post("/evaluate/output", json=payload)
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"]
