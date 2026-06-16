# Release Criteria — v1.2

This technical release is considered ready when:

```text
[x] pytest passes.
[x] /health returns ok.
[x] /system/ready returns ready in local mode.
[x] /agent/chat works for admin, clinical-risk and low-confidence cases.
[x] /dashboard loads.
[x] /metrics endpoints return data after seeding.
[x] /audit returns saved evaluations.
[x] /event-calculus/evaluate works without Clingo via fallback.
[x] PostgreSQL backend starts with docker compose.
[x] README and docs are present.
```
