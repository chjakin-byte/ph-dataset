from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Dict, List, Tuple


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
        ts = (p.get("created_at") or "")[:10]
        if not ts:
            continue
        y, w, _ = date.fromisoformat(ts).isocalendar()
        weeks[f"{y}-W{w:02d}"].update(p.get("topics") or [])
    return {k: Counter(dict(v.most_common(top))) for k, v in sorted(weeks.items())}
