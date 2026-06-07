from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class ProductHuntComment(BaseModel):
    product_slug: str
    comment_text: str
    comment_author: str
    created_date: str
    upvotes: int

class ProductHuntProduct(BaseModel):
    id: str
    slug: str
    product_name: str
    tagline: str
    description: str
    votes: int
    comment_count: int
    topics: List[str]
    launch_date: Optional[str]
    website: str
    makers: List[str] = []
