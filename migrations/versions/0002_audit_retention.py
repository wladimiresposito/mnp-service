"""audit retention support: created_at index for purge jobs

Revision ID: 0002_audit_retention
Revises: 0001_initial
Create Date: 2026-06-14

Adiciona um indice por created_at em mnp_evaluations para suportar
rotinas de retencao/expurgo (Art. 16 LGPD: eliminacao apos o fim do
tratamento). O conteudo sensivel de texto livre ja e minimizado na
camada de masking; a retencao trata do ciclo de vida do registro.
"""
from __future__ import annotations

from alembic import op

revision = "0002_audit_retention"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_eval_created_at ON mnp_evaluations (created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_eval_created_at")
