# Deployment Guide — MNP v1.2

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Docker Compose with PostgreSQL

```bash
docker compose up --build
```

## Required production settings

```env
MNP_REQUIRE_API_KEY=true
MNP_API_KEYS=<rotate-this-secret>
MNP_AUDIT_BACKEND=postgres
MNP_POSTGRES_DSN=postgresql://...
MNP_MASK_SENSITIVE_FIELDS=true
MNP_CORS_ALLOW_ORIGINS=https://your-admin-domain.example
```

## Health and readiness

```text
GET /health
GET /system/live
GET /system/ready
GET /system/version
```

## Dashboard

```text
GET /dashboard
```

For production, put it behind authentication, VPN, SSO or an internal reverse proxy.
