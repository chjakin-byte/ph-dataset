from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class RawEvidence(BaseModel):
    source_platform: str
    source_location: str
    timestamp: datetime
    extracted_text: str
    relevance_score: float = 0.0

class MappedEvidence(RawEvidence):
    module: str  # Market, User, Pain Point, Competitor, Evidence, Launch Strategy, Risk, Final Recommendation
    conclusion: Optional[str] = None
