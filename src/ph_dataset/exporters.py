from __future__ import annotations

import csv
import json
import os
from typing import Dict, List

LIST_FIELDS = ("topics", "makers")


def export(records: List[Dict], path: str, fmt: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    elif fmt == "csv":
        fields = sorted({k for r in records for k in r})
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in records:
                w.writerow({k: ("|".join(v) if k in LIST_FIELDS and isinstance(v, list) else v)
                            for k, v in r.items()})
    elif fmt == "parquet":
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as e:
            raise RuntimeError("Parquet export needs pyarrow: pip install 'ph-dataset[parquet]'") from e
        pq.write_table(pa.Table.from_pylist(records), path)
    else:
        raise ValueError(f"Unknown format: {fmt}")
    return path
