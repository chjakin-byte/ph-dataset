from typing import List, Optional
from pydantic import BaseModel, Field

class PipelineConfig(BaseModel):
    product_name: str
    product_description: str
    target_categories: List[str]
    target_keywords: List[str]
    time_window: str
    source_platforms: List[str]
    output_path: str = "output/kickstarter_research_report.xlsx"
