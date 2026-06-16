# MNP Service v1.2.0 — Technical Release

This is the first hardened technical release of the Pluggable Normative Middleware reference implementation.

## Highlights

```text
- End-to-end agentic/RAG integration
- JSON Schema fact extraction
- Human review fallback
- Tenant-based plugin registry
- SQLite/PostgreSQL audit repositories
- Metrics and operational dashboard
- ASP/Clingo experimental plugin
- Explicit Event Calculus module
- Release hardening middleware
- Operational documentation
```

## Validation

Run:

```bash
pytest -q
```

## Recommended next work

```text
- Replace mock generator with real LLM adapter for plans/drafts.
- Add authenticated dashboard.
- Add Alembic migrations.
- Add tenant management API.
- Add plugin signing/version approval workflow.
- Add production-grade human review UI.
```
