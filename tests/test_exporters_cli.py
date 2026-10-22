import csv
import json

import pytest

from ph_dataset.analysis import topic_trends, weekly_topic_counts
from ph_dataset.cli import main
from ph_dataset.exporters import export
from ph_dataset.store import JsonlStore

RECS = [{"id": "1", "name": "A", "votes": 5, "topics": ["AI", "Dev"], "created_at": "2024-01-01T00:00:00Z"},
        {"id": "2", "name": "B", "votes": 3, "topics": ["AI"], "created_at": "2024-01-09T00:00:00Z"}]


def test_csv_json(tmp_path):
    export(RECS, str(tmp_path / "a.csv"), "csv")
    rows = list(csv.DictReader(open(tmp_path / "a.csv")))
    assert rows[0]["topics"] == "AI|Dev"
    export(RECS, str(tmp_path / "a.json"), "json")
    assert json.load(open(tmp_path / "a.json"))[1]["name"] == "B"


def test_parquet(tmp_path):
    pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq
    export(RECS, str(tmp_path / "a.parquet"), "parquet")
    assert pq.read_table(tmp_path / "a.parquet").num_rows == 2


def test_trends():
    assert topic_trends(RECS)[0] == ("AI", 2, 8)
    assert list(weekly_topic_counts(RECS)) == ["2024-W01", "2024-W02"]


def test_cli_export_and_trends(tmp_path, capsys):
    JsonlStore(str(tmp_path / "products.jsonl")).append(RECS)
    assert main(["--data-dir", str(tmp_path), "export", "--format", "json"]) == 0
    assert main(["--data-dir", str(tmp_path), "trends"]) == 0
    assert "AI" in capsys.readouterr().out


def test_cli_fetch_without_credentials(monkeypatch, tmp_path):
    for k in ("PH_TOKEN", "PH_CLIENT_ID", "PH_CLIENT_SECRET"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.chdir(tmp_path)
    assert main(["fetch", "--since", "2024-01"]) == 2
