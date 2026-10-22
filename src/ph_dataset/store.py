from __future__ import annotations

import json
import os
from typing import Dict, Iterable, List


class JsonlStore:
    """Append-only JSONL store with dedup by id (last write wins on load)."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def append(self, records: Iterable[Dict]) -> int:
        n = 0
        with open(self.path, "a", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += 1
        return n

    def load(self) -> List[Dict]:
        if not os.path.exists(self.path):
            return []
        out: Dict[str, Dict] = {}
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    out[str(r["id"])] = r
        return list(out.values())
