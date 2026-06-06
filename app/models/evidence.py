from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class RawEvidence(BaseModel):
    source_platform: str
    source_location: str
    timestamp: datetime
    extracted_text: str
    evidence_score: float = Field(default=0.0, description="0-100 score based on Source Reliability, Recency, Frequency, Relevance")
    frequency: int = Field(default=1, description="Count of near-duplicate occurrences")

class MappedEvidence(RawEvidence):
    module: str  # Market, User, Pain Points, Competitors, Evidence, Launch Strategy, Risk, Final Recommendation
    conclusion: Optional[str] = None
    
# Kickstarter Specific Models
class KickstarterRewardTier(BaseModel):
    price: float
    quantity_available: Optional[int]
    sold_count: int
    description: str

class KickstarterComment(BaseModel):
    comment_text: str
    comment_time: datetime
    comment_author: str
    reply_exists: bool
    like_count: Optional[int] = 0

class KickstarterProject(BaseModel):
    project_name: str
    category: str
    tags: List[str] = []
    inferred_topic_cluster: str = "Unknown"
    launch_date: Optional[datetime]
    funding_goal: float
    funding_amount: float
    backer_count: int
    funding_percentage: float
    project_description: str
    creator: str
    faq_count: int = 0
    update_count: int = 0
    comments: List[KickstarterComment] = []
    rewards: List[KickstarterRewardTier] = []

# Signal Models
class SignalScore(BaseModel):
    signal_name: str
    signal_score: float = Field(..., description="0-100")
    evidence_references: List[str]
    description: str

# Opportunity Score model is removed for V1.5 to focus on Signal Score and Raw Data
    
class DataQualityMetric(BaseModel):
    metric_name: str
    value: float
    notes: str