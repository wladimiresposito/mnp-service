# Migrações de banco (Alembic)

O esquema de auditoria passou a ser versionado com Alembic, em vez do
`app/audit/postgres_schema.sql` solto. A URL do banco vem de
`MNP_POSTGRES_DSN` (resolvida em `migrations/env.py`, com driver psycopg3).

## Comandos

Aplicar todas as migrações pendentes:

```bash
alembic upgrade head
```

Ver o histórico e a revisão atual:

```bash
alembic history
alembic current
```

Gerar o SQL sem conectar ao banco (útil para revisão em PR ou para rodar
manualmente em um banco gerenciado):

```bash
alembic upgrade head --sql > migration.sql
```

Reverter a última revisão:

```bash
alembic downgrade -1
```

## Revisões

```text
0001_initial         tabelas mnp_evaluations e mnp_plugin_results + indices
0002_audit_retention indice por created_at para rotinas de retencao/expurgo
```

## Criar uma nova revisão

As migrações aqui são escritas à mão (o serviço usa SQL puro via psycopg,
sem modelos declarativos, então `--autogenerate` não se aplica):

```bash
alembic revision -m "descricao curta"
```

Edite o arquivo gerado em `migrations/versions/` preenchendo `upgrade()` e
`downgrade()` com `op.execute(...)`.

## Relação com o schema.sql legado

O `app/audit/postgres_schema.sql` permanece no repositório como referência
e para o bootstrap em SQLite, mas a fonte de verdade do esquema Postgres em
produção passa a ser o conjunto de migrações. A revisão `0001_initial`
reproduz exatamente aquele schema.
