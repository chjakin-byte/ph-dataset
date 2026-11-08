"""Deterministic FAKE Product Hunt-like records for tests, demos and screenshots.

Nothing here is real Product Hunt data: names, votes and dates are generated.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List

FAKE_TOPICS = ["Artificial Intelligence", "Developer Tools", "Productivity", "Marketing",
               "Design Tools", "Fintech", "Health", "Education"]


def fake_products(n: int = 200, seed: int = 42, end: str = "2026-10-19", weeks: int = 16) -> List[Dict]:
    """Return ``n`` fake product dicts spread over ``weeks`` weeks ending at ``end`` (UTC).

    AI launches get more frequent over time and Fintech fewer, so momentum has something to show.
    """
    rng = random.Random(seed)
    end_dt = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    span = weeks * 7 * 24 * 3600
    out: List[Dict] = []
    for i in range(n):
        frac = rng.random() ** 0.8
        created = end_dt - timedelta(seconds=int(span * (1 - frac)))
        weights = [1 + 3 * frac, 2, 2, 1.5, 1, 2.5 * (1 - frac) + 0.2, 1, 1]
        main = rng.choices(FAKE_TOPICS, weights=weights)[0]
        topics = [main]
        if rng.random() < 0.5:
            other = rng.choice(FAKE_TOPICS)
            if other != main:
                topics.append(other)
        base = 40 if created.weekday() < 5 else 25
        votes = int(rng.lognormvariate(0, 1) * base)
        out.append({
            "id": f"fake-{i:04d}",
            "slug": f"fake-product-{i:04d}",
            "name": f"Fake Product {i:04d}",
            "tagline": f"A made-up {main.lower()} tool for demos",
            "description": "",
            "votes": votes,
            "comments_count": int(votes * rng.uniform(0.05, 0.3)),
            "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "featured_at": None,
            "website": "",
            "url": "",
            "topics": topics,
            "makers": [],
            "rating": round(rng.uniform(3.0, 5.0), 1),
        })
    return out
