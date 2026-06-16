# Demo Guide — MNP v1.2

## 1. Start the service

```bash
make install
make dev
```

## 2. Open docs and dashboard

```text
http://localhost:8000/docs
http://localhost:8000/dashboard
```

## 3. Run an end-to-end clinical example

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d @examples/payloads/agent_chat_health_medication.json
```

Expected:

```text
action_taken = modified
verdict.decision = modify
```

## 4. Run low-confidence example

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d @examples/payloads/agent_chat_low_confidence.json
```

Expected:

```text
action_taken = escalated
review_id != null
```

## 5. Run Event Calculus example

```bash
curl -X POST http://localhost:8000/event-calculus/evaluate \
  -H "Content-Type: application/json" \
  -d @examples/payloads/ec_revoked_consent.json
```

Expected:

```text
decision.forbidden = true
violated_rules includes ec_sensitive_processing_without_active_consent
```

## 6. Seed and inspect dashboard

```bash
python examples/seed_dashboard_data.py
```

Refresh:

```text
http://localhost:8000/dashboard
```
