# MNP Service v1.2 — Middleware Normativo Pluggable

Technical release of the **Middleware Normativo Pluggable (MNP)** reference implementation.

The MNP is a governance layer between LLM-based applications and final response/action execution. The LLM interprets, extracts facts, retrieves context and proposes plans/drafts. The MNP evaluates normative permissibility through plugins and returns a structured verdict:

```text
allow | modify | block | escalate
```

## What is included

```text
- FastAPI service
- Tenant-based plugin registry
- JSON Schema fact extraction
- Human review fallback
- Agentic/RAG end-to-end demo
- SQLite/PostgreSQL audit repository
- Metrics endpoints
- Operational dashboard
- Experimental ASP/Clingo plugin
- Explicit Event Calculus module
- Normative tests in YAML
- Release hardening middleware
- Deployment, security and operations docs
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
http://localhost:8000/dashboard
```

## Run tests

```bash
pytest -q
```

## Smoke test

Start the server, then:

```bash
python scripts/smoke_test.py
```

## Seed dashboard data

```bash
python examples/seed_dashboard_data.py
```

## Docker Compose with PostgreSQL

```bash
docker compose up --build
```

## Important endpoints

```text
GET  /health
GET  /system/live
GET  /system/ready
GET  /system/version

GET  /dashboard

POST /agent/chat
POST /rag/search
POST /extract/facts
GET  /extract/schema

POST /evaluate/input
POST /evaluate/plan
POST /evaluate/tool-call
POST /evaluate/output
POST /evaluate/all

GET  /audit
GET  /metrics/summary
GET  /metrics/rules
GET  /metrics/plugins

GET  /human-review/pending
POST /human-review/{review_id}/resolve

GET  /asp/status
POST /asp/temporal-consent

GET  /event-calculus/status
POST /event-calculus/evaluate
```

## Documentation

```text
docs/ARCHITECTURE.md
docs/DEPLOYMENT.md
docs/SECURITY_CHECKLIST.md
docs/OPERATIONS_RUNBOOK.md
docs/DEMO_GUIDE.md
docs/RELEASE_CRITERIA.md
CHANGELOG.md
RELEASE_NOTES.md
```

## Production warning

This is a technical reference implementation. Before production use:

```text
- enable API key authentication;
- put the dashboard behind proper authentication;
- use PostgreSQL;
- add gateway rate limiting;
- review plugin rules with legal/domain experts;
- define retention policies for audit and human review data;
- add migration tooling such as Alembic.
```
