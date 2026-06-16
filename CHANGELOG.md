# Changelog

## v1.2.0

Camada de teste sintetico (diferencial + metamorfico) sobre os dois motores.

```text
- Gerador deterministico de cenarios (app/testing/synthetic.py), corpus
  reproduzivel por seed para auditabilidade.
- Teste diferencial clingo vs fallback sobre o corpus sintetico, e testes
  metamorficos (evento futuro inerte, relaxar base legal nao endurece,
  emergencia so relaxa).
- scripts/divergence_report.py: relatorio de divergencia em larga escala.
- Reconciliacao dos dois motores guiada pelos achados do gerador: escopo de
  confirmacao de proposito, fluente purpose_confirmed, guarda de tempo no
  breach (corrige contagem de evento futuro), escalonamento por incidente,
  obrigacao obl_confirm_purpose. Resultado: 0 divergencias em 35k cenarios.
- CI: gate de divergencia 0 e bloqueio se a cross-validacao for pulada.
- docs/SYNTHETIC_TESTING.md: posicao sobre casos vs regras sinteticas e
  questoes normativas em aberto (eventos de revisao humana, convencao de
  tempo do breach).
```

## v1.1.0

Correcao de bugs no nucleo neuro-simbolico e melhorias de robustez,
seguindo a revisao tecnica. O "40 passed" anterior so ocorria sem clingo
instalado (tudo caia no fallback); com clingo presente, 10 testes falhavam.

```text
Correcoes (bugs):
- ASP grounding: variaveis de tempo T/T0 agora vinculadas a time/1 nos
  axiomas de Event Calculus (10_event_calculus.lp e temporal_asp/base.lp).
  Antes o clingo recusava o grounding (unsafe variables).
- Estado de fluente reportado fora do tempo: consent_holds agora e
  consultado em current_time, nao "em algum instante". A trilha nao
  contradiz mais a decisao.
- consequence_id: prefixo cons_ alinhado ao contrato da API.
- Proveniencia: initiated_by/clipped_by populados no estado do fluente.
- violated_rule/required_change amarrados a causa especifica da proibicao
  (consentimento vs proposito), nos dois motores (clingo e fallback).

Melhorias:
- Cross-validacao automatica clingo vs fallback (tests/test_cross_validation).
- Composicao hierarquica + flag binding (vinculante vs suplementar).
- Minimizacao de texto livre na auditoria (hash+comprimento, nao em claro).
- Migracoes Alembic (0001 inicial, 0002 indice de retencao).
- Extractor LLM com retry/backoff, JSON mode e teste com rede mockada.
- CI com clingo obrigatorio e gate contra cross-validacao pulada.
```

## v1.0.0

Technical release hardening:

```text
- System endpoints: /system/version, /system/live, /system/ready
- Request ID middleware
- Basic security headers
- Optional CORS configuration
- Request body size guard
- Makefile
- Smoke test script
- OpenAPI export script
- Architecture, deployment, security, operations and demo docs
- Release checklist
```

## v0.9.0

Operational dashboard.

## v0.8.0

Explicit Event Calculus module.

## v0.7.0

Experimental ASP/Clingo plugin.

## v0.6.0

Agentic/RAG end-to-end flow.

## v0.5.0

LLM fact extractor with JSON Schema and human review fallback.

## v0.4.0

PostgreSQL audit repository and metrics.

## v0.3.0

Tenant plugin registry and YAML normative tests.

## v0.2.0

FastAPI MVP.

## v0.1.0

Python prototype.
