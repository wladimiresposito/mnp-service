# Operations Runbook — MNP v1.2

## Start locally

```bash
make install
make dev
```

## Run tests

```bash
make test
```

## Run smoke test

Start the server first:

```bash
make dev
```

Then:

```bash
make smoke
```

## Seed dashboard data

```bash
make seed
```

Open:

```text
http://localhost:8000/dashboard
```

## Export OpenAPI schema

```bash
make openapi
```

Output:

```text
docs/openapi.json
```

## Diagnose degraded readiness

Call:

```bash
curl http://localhost:8000/system/ready
```

Check:

```text
- audit_repository
- tenant_registry
- plugins_registered
- tenants_configured
```

## Typical incidents

### Audit backend unavailable

Symptoms:

```text
/system/ready returns degraded
/evaluate endpoints may fail when saving audit
```

Actions:

```text
1. Check PostgreSQL connection string.
2. Check container health.
3. Check credentials.
4. Fall back to SQLite only for local/dev.
```

### Human review queue growing

Actions:

```text
1. Inspect /human-review/pending.
2. Identify low-confidence extractor cases.
3. Improve fact extraction prompt or schema.
4. Add domain-specific rules.
```
