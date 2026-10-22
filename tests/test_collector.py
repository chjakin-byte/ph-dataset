from datetime import date

import pytest

from conftest import FakeSession, Resp
from ph_dataset.client import APIError, PHClient
from ph_dataset.collector import Collector


def node(i, day="2024-01-01", comments=0):
    return {"id": str(i), "slug": f"p{i}", "name": f"P{i}", "votesCount": i, "commentsCount": comments,
            "createdAt": f"{day}T10:00:00Z", "topics": {"edges": [{"node": {"name": "AI"}}]},
            "makers": [{"name": "Alice"}]}


def page(nodes, has_next=False, cursor="c"):
    return Resp(200, {"data": {"posts": {"pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                                         "edges": [{"node": n} for n in nodes]}}})


def make(tmp_path, responses, **kw):
    s = FakeSession(responses)
    return Collector(PHClient(token="t", session=s, sleep=lambda _: None), str(tmp_path), **kw), s


def test_fetch_paginates_and_dedups(tmp_path):
    c, s = make(tmp_path, [page([node(1), node(2)], True, "c1"), page([node(2), node(3)])])
    assert c.fetch(date(2024, 1, 1), date(2024, 1, 2)) == 4
    prods = c.products.load()
    assert sorted(p["id"] for p in prods) == ["1", "2", "3"]
    assert s.calls[1]["json"]["variables"]["after"] == "c1"
    assert c.state.get("completed_through") == "2024-01-01"


def test_makers_opt_in(tmp_path):
    c, s = make(tmp_path, [page([node(1)])])
    c.fetch(date(2024, 1, 1), date(2024, 1, 2))
    assert c.products.load()[0]["makers"] == []
    assert "makers" not in s.calls[0]["json"]["query"]
    c2, s2 = make(tmp_path / "m", [page([node(1)])], include_makers=True)
    c2.fetch(date(2024, 1, 1), date(2024, 1, 2))
    assert c2.products.load()[0]["makers"] == ["Alice"]


def test_resume_after_failure(tmp_path):
    c, _ = make(tmp_path, [page([node(1)]), page([node(2)], True, "c2"), Resp(400, text="boom")])
    with pytest.raises(APIError):
        c.fetch(date(2024, 1, 1), date(2024, 1, 3))
    assert c.state.get("completed_through") == "2024-01-01"
    assert c.state.get("cursor") == "c2"
    c2, s2 = make(tmp_path, [page([node(3)])])
    c2.fetch(date(2024, 1, 1), date(2024, 1, 3))
    v = s2.calls[0]["json"]["variables"]
    assert v["after"] == "c2" and v["postedAfter"].startswith("2024-01-02")
    assert c2.state.get("completed_through") == "2024-01-02"


def test_comments_opt_in(tmp_path):
    com = Resp(200, {"data": {"post": {"comments": {"pageInfo": {"hasNextPage": False},
               "edges": [{"node": {"id": "k1", "body": "nice", "votesCount": 2}}]}}}})
    c, _ = make(tmp_path, [page([node(1, comments=1)]), com], include_comments=True)
    c.fetch(date(2024, 1, 1), date(2024, 1, 2))
    assert c.comments.load()[0]["product_id"] == "1"


def test_update_continues_from_state(tmp_path):
    c, s = make(tmp_path, [page([])] * 2)
    c.state.set(completed_through="2024-01-01")
    c.update(today=date(2024, 1, 4))
    assert [x["json"]["variables"]["postedAfter"][:10] for x in s.calls] == ["2024-01-02", "2024-01-03"]
    assert c.state.get("completed_through") == "2024-01-03"  # today (01-04) not marked done


def test_max_products_is_exact(tmp_path):
    c, s = make(tmp_path, [page([node(i) for i in range(1, 21)], True, "c1")])
    assert c.fetch(date(2024, 1, 1), date(2024, 1, 2), max_products=5) == 5
    assert len(c.products.load()) == 5 and len(s.calls) == 1


def test_featured_only_and_stable_order(tmp_path):
    c, s = make(tmp_path, [page([node(1)])], featured_only=True)
    c.fetch(date(2024, 1, 1), date(2024, 1, 2))
    call = s.calls[0]["json"]
    assert call["variables"]["featured"] is True and "order: NEWEST" in call["query"]
    c2, s2 = make(tmp_path / "b", [page([node(1)])])
    c2.fetch(date(2024, 1, 1), date(2024, 1, 2))
    assert s2.calls[0]["json"]["variables"]["featured"] is None
