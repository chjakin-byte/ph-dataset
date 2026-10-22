from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from .client import PHClient
from .models import map_comment, map_post
from .state import State
from .store import JsonlStore

log = logging.getLogger(__name__)

POSTS_QUERY = """
query($after: String, $postedAfter: DateTime!, $postedBefore: DateTime!, $topic: String, $featured: Boolean) {
  posts(first: 20, after: $after, postedAfter: $postedAfter, postedBefore: $postedBefore, topic: $topic,
        featured: $featured, order: NEWEST) {
    pageInfo { hasNextPage endCursor }
    edges { node {
      id slug name tagline description votesCount commentsCount createdAt featuredAt website url
      topics(first: 10) { edges { node { name } } }
      %MAKERS%
    } }
  }
}
"""

COMMENTS_QUERY = """
query($id: ID!, $after: String) {
  post(id: $id) { comments(first: 20, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node { id body votesCount createdAt } }
  } }
}
"""


class Collector:
    def __init__(self, client: PHClient, out_dir: str = "data", include_makers: bool = False,
                 include_comments: bool = False, max_comments: int = 50, topic: Optional[str] = None,
                 featured_only: bool = False):
        self.client = client
        self.out_dir = out_dir
        self.include_makers = include_makers
        self.include_comments = include_comments
        self.max_comments = max_comments
        self.topic = topic
        self.featured_only = featured_only
        self.products = JsonlStore(os.path.join(out_dir, "products.jsonl"))
        self.comments = JsonlStore(os.path.join(out_dir, "comments.jsonl"))
        self.state = State(os.path.join(out_dir, "state.json"))

    def _posts_query(self) -> str:
        return POSTS_QUERY.replace("%MAKERS%", "makers { name }" if self.include_makers else "")

    def fetch(self, since: date, until: date, max_products: Optional[int] = None) -> int:
        """Collect posts day by day in [since, until). Resumes from saved state."""
        day = since
        done = self.state.get("completed_through")
        if done:
            day = max(day, date.fromisoformat(done) + timedelta(days=1))
        total = 0
        while day < until:
            cursor = self.state.get("cursor") if self.state.get("cursor_day") == day.isoformat() else None
            while True:
                data = self.client.query(self._posts_query(), {
                    "after": cursor, "topic": self.topic, "featured": True if self.featured_only else None,
                    "postedAfter": _iso(day), "postedBefore": _iso(day + timedelta(days=1))})
                posts = data.get("posts") or {}
                batch = [map_post(e["node"], self.include_makers) for e in posts.get("edges", [])]
                if max_products:
                    batch = batch[: max_products - total]
                self.products.append(p.to_dict() for p in batch)
                if self.include_comments:
                    for p in batch:
                        if p.comments_count:
                            self.comments.append(c.to_dict() for c in self._comments(p.id))
                total += len(batch)
                info = posts.get("pageInfo") or {}
                cursor = info.get("endCursor")
                self.state.set(cursor_day=day.isoformat(), cursor=cursor)
                if max_products and total >= max_products:
                    log.info("Reached max_products=%s", max_products)
                    return total
                if not info.get("hasNextPage"):
                    break
            self.state.set(completed_through=day.isoformat(), cursor=None, cursor_day=None)
            log.info("Completed %s (%s products so far)", day, total)
            day += timedelta(days=1)
        return total

    def update(self, today: Optional[date] = None, max_products: Optional[int] = None) -> int:
        """Fetch completed UTC days after the last completed day (default: last 7 days) up to yesterday.

        Today is skipped because it is still in progress; it is picked up by the next run.
        """
        today = today or datetime.now(timezone.utc).date()
        done = self.state.get("completed_through")
        since = date.fromisoformat(done) + timedelta(days=1) if done else today - timedelta(days=7)
        return self.fetch(since, today, max_products)

    def _comments(self, post_id: str) -> List:
        out, cursor = [], None
        while len(out) < self.max_comments:
            data = self.client.query(COMMENTS_QUERY, {"id": post_id, "after": cursor})
            conn = ((data.get("post") or {}).get("comments")) or {}
            out += [map_comment(e["node"], post_id) for e in conn.get("edges", [])]
            info = conn.get("pageInfo") or {}
            if not info.get("hasNextPage"):
                break
            cursor = info.get("endCursor")
        return out[: self.max_comments]


def _iso(d: date) -> str:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
