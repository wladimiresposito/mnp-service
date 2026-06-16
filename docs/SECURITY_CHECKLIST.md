# Security Checklist — MNP v1.2

Before exposing this service outside a local environment:

```text
[ ] Set MNP_REQUIRE_API_KEY=true.
[ ] Use strong API keys and rotate them.
[ ] Use PostgreSQL instead of SQLite.
[ ] Put the service behind TLS.
[ ] Restrict /dashboard to internal networks or authenticated users.
[ ] Configure CORS explicitly.
[ ] Confirm sensitive-field masking.
[ ] Set a strong MNP_AUDIT_TEXT_HASH_SALT (free-text minimization pepper).
[ ] Confirm free-text minimization is on (MNP_MINIMIZE_FREE_TEXT=true).
[ ] Run Alembic migrations (alembic upgrade head) instead of raw schema.sql.
[ ] Avoid logging raw LLM prompts that contain secrets or sensitive data.
[ ] Review tenant plugin configuration.
[ ] Run normative YAML tests before deploying plugin changes.
[ ] Review OpenAI-compatible extractor configuration if used.
[ ] Add rate limiting at gateway/reverse proxy.
[ ] Add backup and retention policy for audit database.
[ ] Add explicit data-retention rules for human_review.jsonl if used.
```

## Known non-goals

This release is not a complete legal compliance product. It is a technical architecture and working reference implementation.
