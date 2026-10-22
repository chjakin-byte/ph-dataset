from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Product:
    id: str
    slug: str
    name: str
    tagline: str = ""
    description: str = ""
    votes: int = 0
    comments_count: int = 0
    created_at: str = ""
    featured_at: Optional[str] = None
    website: str = ""
    url: str = ""
    topics: List[str] = field(default_factory=list)
    makers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Comment:
    id: str
    product_id: str
    body: str = ""
    votes: int = 0
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def map_post(node: Dict[str, Any], include_makers: bool = False) -> Product:
    """Map a GraphQL Post node to a Product."""
    topics = [e.get("node", {}).get("name") for e in (node.get("topics") or {}).get("edges", [])]
    makers = [m.get("name") for m in (node.get("makers") or [])] if include_makers else []
    return Product(
        id=str(node.get("id", "")),
        slug=node.get("slug") or "",
        name=node.get("name") or "",
        tagline=node.get("tagline") or "",
        description=node.get("description") or "",
        votes=int(node.get("votesCount") or 0),
        comments_count=int(node.get("commentsCount") or 0),
        created_at=node.get("createdAt") or "",
        featured_at=node.get("featuredAt"),
        website=node.get("website") or "",
        url=node.get("url") or "",
        topics=[t for t in topics if t],
        makers=[m for m in makers if m],
    )


def map_comment(node: Dict[str, Any], product_id: str) -> Comment:
    return Comment(
        id=str(node.get("id", "")),
        product_id=product_id,
        body=node.get("body") or "",
        votes=int(node.get("votesCount") or 0),
        created_at=node.get("createdAt") or "",
    )
