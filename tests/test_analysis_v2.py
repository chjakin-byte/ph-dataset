import sqlite3

import pytest

from ph_dataset.analysis import best_time, momentum, percentile_rank, quantile, score_product, score_votes
from ph_dataset.cli import main
from ph_dataset.demo import fake_products
from ph_dataset.exporters import export
from ph_dataset.store import JsonlStore

FAKE = [
    {"id": "1", "slug": "a", "votes": 10, "topics": ["AI"], "created_at": "2026-01-05T08:00:00Z"},  # Mon
    {"id": "2", "slug": "b", "votes": 20, "topics": ["AI"], "created_at": "2026-01-06T08:00:00Z"},  # Tue
    {"id": "3", "slug": "c", "votes": 30, "topics": ["AI", "Dev"], "created_at": "2026-01-26T08:00:00Z"},
    {"id": "4", "slug": "d", "votes": 40, "topics": ["AI"], "created_at": "2026-01-27T08:00:00Z"},
    {"id": "5", "slug": "e", "votes": 50, "topics": ["AI"], "created_at": "2026-01-28T08:00:00Z"},
]


def test_quantile_and_rank():
    assert quantile([1, 2, 3, 4], 0.5) == 2.5
    assert quantile([], 0.9) == 0.0
    assert percentile_rank([10, 20, 30, 40], 30) == 62.5


def test_score():
    r = score_votes(FAKE, 35, "ai")
    assert r["sample"] == 5 and r["percentile"] == 60.0 and r["median"] == 30
    assert [x["topic"] for x in score_product(FAKE, "c")] == ["AI", "Dev"]
    with pytest.raises(KeyError):
        score_product(FAKE, "zzz")


def test_momentum():
    res = momentum(FAKE, weeks=2)
    ai = next(x for x in res["rising"] if x["topic"] == "AI")
    assert ai["recent"] == 3 and ai["previous"] == 2 and ai["growth"] == 0.5


def test_best_time():
    rows = best_time(FAKE)
    assert rows[0]["weekday"] == "Monday" and rows[0]["launches"] == 2 and rows[0]["median_votes"] == 20


def test_sqlite_export(tmp_path):
    export(FAKE, str(tmp_path / "p.db"), "sqlite")
    con = sqlite3.connect(tmp_path / "p.db")
    assert con.execute("select sum(votes) from products").fetchone()[0] == 150
    assert con.execute("select topics from products where id='3'").fetchone()[0] == "AI|Dev"


def test_duckdb_export(tmp_path):
    duckdb = pytest.importorskip("duckdb")
    export(FAKE, str(tmp_path / "p.duckdb"), "duckdb")
    con = duckdb.connect(str(tmp_path / "p.duckdb"))
    assert con.execute("select count(*) from products").fetchone()[0] == 5


def test_fake_generator_is_fake_and_stable():
    a, b = fake_products(50), fake_products(50)
    assert a == b and all(p["name"].startswith("Fake Product") for p in a)


def test_cli_v2_commands(tmp_path, capsys):
    JsonlStore(str(tmp_path / "products.jsonl")).append(fake_products(120))
    d = ["--data-dir", str(tmp_path)]
    assert main(d + ["score", "--votes", "50", "--topic", "artificial-intelligence"]) == 0
    assert main(d + ["score", "--product", "fake-product-0001"]) == 0
    assert main(d + ["score", "--product", "nope"]) == 1
    assert main(d + ["score", "--votes", "5"]) == 2
    assert main(d + ["momentum", "--weeks", "4"]) == 0
    assert main(d + ["best-time"]) == 0
    out = capsys.readouterr().out
    assert "beats" in out and "RISING" in out and "Correlation, not causation" in out


def test_cli_no_data(tmp_path, capsys):
    assert main(["--data-dir", str(tmp_path), "momentum"]) == 1
    assert "No data yet" in capsys.readouterr().out
