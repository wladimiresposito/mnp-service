# MNP Architecture — Technical Release v1.2

## Core idea

The Middleware Normativo Pluggable separates two concerns:

```text
LLM/application:
  interpret context, extract facts, retrieve knowledge, propose plans and drafts.

MNP:
  evaluate normative permissibility and return structured verdicts.
```

## Runtime flow

```text
User
  ↓
/agent/chat
  ↓
Fact extraction
  ↓
RAG search
  ↓
Agent plan / tool call / draft
  ↓
MNP evaluate_all
  ↓
Plugins
  ↓
Composition engine
  ↓
allow | modify | block | escalate
  ↓
Final answer or human review
  ↓
Audit repository
  ↓
Dashboard
```

## Main packages

```text
app/core             Domain models, plugin interface, middleware, composition
app/plugins          Normative plugins
app/extraction       JSON Schema fact extraction
app/review           Human review queue
app/rag              Local demo RAG
app/agent            End-to-end orchestration
app/audit            SQLite/PostgreSQL audit repositories
app/event_calculus   Explicit Event Calculus module
app/asp              Experimental ASP/Clingo adapter
app/dashboard        Operational HTML dashboard
```

## Plugin contract

Each plugin implements:

```python
evaluate_input(context)
evaluate_plan(plan)
evaluate_tool_call(tool_call)
evaluate_output(draft)
metadata()
```

The output is always a structured `Verdict`.
