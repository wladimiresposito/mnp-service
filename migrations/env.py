"""Ambiente de migracao Alembic do MNP.

A URL do banco vem de settings (MNP_POSTGRES_DSN). Como o servico usa
psycopg3, normalizamos o dialeto para 'postgresql+psycopg'. Suporta modo
offline (gera SQL sem conectar) e online.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config.settings import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _database_url() -> str:
    dsn = settings.postgres_dsn
    # Garante o driver psycopg3 explicitamente para o SQLAlchemy.
    if dsn.startswith("postgresql://"):
        dsn = dsn.replace("postgresql://", "postgresql+psycopg://", 1)
    return dsn


# Sem metadata declarativa: as migracoes sao escritas a mao (o servico usa
# SQL puro via psycopg). autogenerate nao se aplica aqui.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
