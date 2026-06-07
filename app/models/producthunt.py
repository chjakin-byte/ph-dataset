from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class ProductHuntProduct(BaseModel):
    product_name: str
    tagline: str
    description: str
    votes: int
    comment_count: int
    topics: List[str]
    launch_date: Optional[str]
    website: str
    makers: List[str] = []
