# Copyright 2026 Wladimir Esposito (OmniAI / Omni Tech Consulting)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
