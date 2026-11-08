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
    elif fmt in ("sqlite", "duckdb"):
        _export_sql(records, path, fmt)
    else:
        raise ValueError(f"Unknown format: {fmt}")
    return path


def _rows(records: List[Dict]):
    fields = sorted({k for r in records for k in r}) or ["id"]
    rows = [tuple(("|".join(v) if isinstance(v, list) else v) for v in (r.get(k) for k in fields))
            for r in records]
    return fields, rows


def _export_sql(records: List[Dict], path: str, fmt: str) -> None:
    """Write a single ``products`` table (lists joined with '|'). Overwrites the table."""
    fields, rows = _rows(records)
    cols = ", ".join(f'"{f}"' for f in fields)
    marks = ", ".join("?" for _ in fields)
    if fmt == "sqlite":
        import sqlite3
        con = sqlite3.connect(path)
    else:
        try:
            import duckdb
        except ImportError as e:
            raise RuntimeError("DuckDB export needs duckdb: pip install 'ph-dataset[duckdb]'") from e
        con = duckdb.connect(path)
    try:
        con.execute("DROP TABLE IF EXISTS products")
        ints = [all(isinstance(r[i], int) or r[i] is None for r in rows) and bool(rows)
                for i in range(len(fields))]
        types = ", ".join(f'"{f}" {"BIGINT" if ints[i] else "VARCHAR"}' for i, f in enumerate(fields))
        con.execute(f"CREATE TABLE products ({types})")
        if rows:
            con.executemany(f"INSERT INTO products ({cols}) VALUES ({marks})",
                            [tuple(v if (ints[i] or v is None) else str(v) for i, v in enumerate(r))
                             for r in rows])
        con.commit()
    finally:
        con.close()
