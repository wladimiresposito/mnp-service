#!/usr/bin/env python3
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

"""Insere o cabeçalho de licença Apache 2.0 em todos os arquivos .py do projeto.

Características:
  - Idempotente: pula arquivos que já contêm o cabeçalho (não duplica).
  - Respeita shebang (#!/usr/bin/env python) e linha de encoding (PEP 263),
    inserindo o cabeçalho logo abaixo delas.
  - Ignora diretórios de ambiente, cache e build.
  - Pula arquivos vazios (ex.: __init__.py sem conteúdo), salvo --include-empty.
  - Modo --dry-run mostra o que mudaria sem escrever nada.

Uso:
    python add_license_header.py                 # aplica na pasta atual
    python add_license_header.py caminho/do/repo # aplica em outra pasta
    python add_license_header.py --dry-run       # só mostra, não escreve
    python add_license_header.py --include-empty # inclui arquivos vazios
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

COPYRIGHT = "Copyright 2026 Wladimir Esposito (OmniAI / Omni Tech Consulting)"

HEADER_LINES = [
    f"# {COPYRIGHT}",
    "#",
    '# Licensed under the Apache License, Version 2.0 (the "License");',
    "# you may not use this file except in compliance with the License.",
    "# You may obtain a copy of the License at",
    "#",
    "#     http://www.apache.org/licenses/LICENSE-2.0",
    "#",
    "# Unless required by applicable law or agreed to in writing, software",
    '# distributed under the License is distributed on an "AS IS" BASIS,',
    "# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.",
    "# See the License for the specific language governing permissions and",
    "# limitations under the License.",
]

# Marcador usado para detectar se o cabeçalho já existe (idempotência).
MARKER = "Licensed under the Apache License, Version 2.0"

EXCLUDE_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env", ".env",
    "build", "dist", ".eggs", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
}

ENCODING_RE = re.compile(r"^#.*coding[:=]\s*[-\w.]+")


def build_header() -> str:
    return "\n".join(HEADER_LINES) + "\n\n"


def needs_header(text: str) -> bool:
    # Só procura nas primeiras linhas para não confundir com o conteúdo.
    head = "\n".join(text.splitlines()[:25])
    return MARKER not in head


def insert_header(text: str, header: str) -> str:
    lines = text.splitlines(keepends=True)
    idx = 0
    # Preserva shebang na primeira linha.
    if lines and lines[0].startswith("#!"):
        idx = 1
    # Preserva linha de encoding (PEP 263) logo abaixo.
    if idx < len(lines) and ENCODING_RE.match(lines[idx].lstrip("\ufeff")):
        idx += 1
    prefix = "".join(lines[:idx])
    rest = "".join(lines[idx:])
    # Garante uma linha em branco entre o cabeçalho e o restante já é dada pelo header.
    return prefix + header + rest


def iter_py_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        if any(part in EXCLUDE_DIRS or part.endswith(".egg-info") for part in path.parts):
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Insere cabeçalho Apache 2.0 nos .py")
    parser.add_argument("path", nargs="?", default=".", help="raiz do projeto")
    parser.add_argument("--dry-run", action="store_true", help="não escreve, só lista")
    parser.add_argument("--include-empty", action="store_true",
                        help="também processa arquivos vazios")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"Caminho não encontrado: {root}", file=sys.stderr)
        return 2

    header = build_header()
    changed = skipped_existing = skipped_empty = 0

    for path in iter_py_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            print(f"  ! pulei (não consegui ler): {path} ({exc})", file=sys.stderr)
            continue

        if not text.strip() and not args.include_empty:
            skipped_empty += 1
            continue
        if not needs_header(text):
            skipped_existing += 1
            continue

        new_text = insert_header(text, header)
        rel = path.relative_to(root)
        if args.dry_run:
            print(f"  + adicionaria: {rel}")
        else:
            path.write_text(new_text, encoding="utf-8")
            print(f"  + cabeçalho inserido: {rel}")
        changed += 1

    verbo = "seriam alterados" if args.dry_run else "alterados"
    print(
        f"\nResumo: {changed} {verbo}, "
        f"{skipped_existing} já tinham o cabeçalho, "
        f"{skipped_empty} vazios pulados."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
