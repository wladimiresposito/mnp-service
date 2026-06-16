from __future__ import annotations

import json
from pathlib import Path

from app.main import app


def main() -> None:
    out = Path("docs/openapi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Exported {out}")


if __name__ == "__main__":
    main()
