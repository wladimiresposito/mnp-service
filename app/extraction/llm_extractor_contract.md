# LLM Fact Extractor Contract — v0.5

A camada de extração de fatos transforma linguagem natural em fatos normativamente relevantes.

Ela não decide se uma ação deve ser permitida, modificada, bloqueada ou escalada.

## Instrução base

```text
Extraia apenas fatos normativamente relevantes.
Não tome decisão normativa.
Não dê conselho.
Não recomende ação.
Não bloqueie nem permita.
Retorne apenas JSON válido conforme o schema.
Se estiver incerto, reduza fact_extraction_confidence e preencha uncertainty_reasons.
```

## Schema canônico

O schema é gerado por:

```python
NormativeFacts.model_json_schema()
```

Endpoint:

```text
GET /extract/schema
```

## Política de confiança

```text
Se fact_extraction_confidence < MNP_FACT_CONFIDENCE_THRESHOLD:
    requires_human_review = true
    fallback_reason = low_fact_extraction_confidence
```

## Falha de validação

```text
Se o LLM retornar JSON inválido ou fora do schema:
    valid = false
    requires_human_review = true
    fallback_reason = fact_extraction_validation_failed
```

## Separação de responsabilidades

```text
LLM Fact Extractor:
    extrai fatos

MNP Plugins:
    decidem allow | modify | block | escalate

Human Review:
    corrige ou aprova fatos quando há baixa confiança ou falha de validação
```
