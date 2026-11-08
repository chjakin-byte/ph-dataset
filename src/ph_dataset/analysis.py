"""Pure analysis functions. They only read records already on disk; no API calls."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _day(p: Dict) -> Optional[date]:
    ts = (p.get("created_at") or "")[:10]
    try:
        return date.fromisoformat(ts) if ts else None
    except ValueError:
        return None


def iso_week(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def topic_trends(products: List[Dict], top: int = 10) -> List[Tuple[str, int, int]]:
    """Per topic: (topic, launches, total votes), sorted by launches."""
    launches, votes = Counter(), defaultdict(int)
    for p in products:
        for t in p.get("topics") or []:
            launches[t] += 1
            votes[t] += int(p.get("votes") or 0)
    return [(t, n, votes[t]) for t, n in launches.most_common(top)]


def weekly_topic_counts(products: List[Dict], top: int = 5) -> Dict[str, Counter]:
    """ISO week (YYYY-Www) -> Counter of topics."""
    weeks: Dict[str, Counter] = defaultdict(Counter)
    for p in products:
        d = _day(p)
        if d:
            weeks[iso_week(d)].update(p.get("topics") or [])
    return {k: Counter(dict(v.most_common(top))) for k, v in sorted(weeks.items())}


def quantile(values: Sequence[float], q: float) -> float:
    """Linear-interpolated quantile (0 <= q <= 1). Empty input returns 0."""
    xs = sorted(values)
    if not xs:
        return 0.0
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return float(xs[lo] + (xs[hi] - xs[lo]) * (pos - lo))


def percentile_rank(values: Sequence[float], x: float) -> float:
    """Share (0-100) of values strictly below x, counting ties as half."""
    if not values:
        return 0.0
    below = sum(1 for v in values if v < x)
    equal = sum(1 for v in values if v == x)
    return round(100.0 * (below + 0.5 * equal) / len(values), 1)


def topic_votes(products: List[Dict], topic: str) -> List[int]:
    t = topic.lower()
    return [int(p.get("votes") or 0) for p in products
            if any(t == x.lower() or t == x.lower().replace(" ", "-") for x in p.get("topics") or [])]


def score_votes(products: List[Dict], votes: int, topic: str) -> Dict:
    """Where does ``votes`` sit among launches in ``topic``?"""
    vals = topic_votes(products, topic)
    return {"topic": topic, "votes": votes, "sample": len(vals),
            "percentile": percentile_rank(vals, votes),
            "median": quantile(vals, 0.5), "p90": quantile(vals, 0.9)}


def score_product(products: List[Dict], slug: str) -> List[Dict]:
    """Score one product (by slug or id) inside each of its topics."""
    p = next((x for x in products if x.get("slug") == slug or str(x.get("id")) == slug), None)
    if p is None:
        raise KeyError(slug)
    return [score_votes(products, int(p.get("votes") or 0), t) for t in p.get("topics") or []]


def momentum(products: List[Dict], weeks: int = 4, top: int = 10,
             today: Optional[date] = None) -> Dict[str, List[Dict]]:
    """Compare launches per topic in the last ``weeks`` weeks vs the ``weeks`` before.

    ``today`` defaults to the newest launch date in the data. Growth is
    (recent - previous) / max(previous, 1). Returns {"rising": [...], "falling": [...]}.
    """
    days = [d for d in (_day(p) for p in products) if d]
    if not days:
        return {"rising": [], "falling": []}
    end = (today or max(days)) + timedelta(days=1)
    mid = end - timedelta(weeks=weeks)
    start = mid - timedelta(weeks=weeks)
    recent, prev = Counter(), Counter()
    for p in products:
        d = _day(p)
        if not d or d < start or d >= end:
            continue
        (recent if d >= mid else prev).update(p.get("topics") or [])
    rows = []
    for t in set(recent) | set(prev):
        r, b = recent[t], prev[t]
        rows.append({"topic": t, "recent": r, "previous": b, "growth": round((r - b) / max(b, 1), 3)})
    rising = sorted([x for x in rows if x["growth"] > 0], key=lambda x: (-x["growth"], -x["recent"]))[:top]
    falling = sorted([x for x in rows if x["growth"] < 0], key=lambda x: (x["growth"], -x["previous"]))[:top]
    return {"rising": rising, "falling": falling}


def best_time(products: List[Dict]) -> List[Dict]:
    """Median votes and launch count per UTC weekday (Monday first). Correlation, not causation."""
    by: Dict[int, List[int]] = defaultdict(list)
    for p in products:
        ts = p.get("created_at") or ""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        by[dt.weekday()].append(int(p.get("votes") or 0))
    return [{"weekday": WEEKDAYS[i], "launches": len(by[i]), "median_votes": quantile(by[i], 0.5)}
            for i in range(7)]


__all__ = ["topic_trends", "weekly_topic_counts", "quantile", "percentile_rank", "score_votes",
           "score_product", "momentum", "best_time", "iso_week"]
