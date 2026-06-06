from typing import List, Dict, Any
from app.models.evidence import KickstarterProject, DataQualityMetric
from datetime import datetime

class QualityAnalyzer:
    def __init__(self):
        pass

    def calculate_evidence_score(self, source_reliability: float, recency_days: int, frequency: int) -> float:
        # Base score out of 100
        score = source_reliability * 40
        
        # Recency decay (newer is better)
        recency_score = max(0, 30 - (recency_days * 0.1)) 
        score += recency_score
        
        # Frequency bonus (more people saying it = stronger signal)
        freq_score = min(30, frequency * 5)
        score += freq_score
        
        return min(100.0, score)

    def generate_quality_metrics(self, raw_projects: int, expected_projects: int, 
                               cleaned_comments: int, total_raw_comments: int,
                               missing_fields_count: int, total_fields_checked: int) -> List[DataQualityMetric]:
        metrics = []
        
        # Crawl Success Rate
        success_rate = (raw_projects / expected_projects) * 100 if expected_projects > 0 else 0
        metrics.append(DataQualityMetric(
            metric_name="Crawl Success Rate",
            value=success_rate,
            notes=f"Successfully fetched {raw_projects} out of {expected_projects} targeted projects."
        ))
        
        # Duplicate Rate
        duplicate_rate = ((total_raw_comments - cleaned_comments) / total_raw_comments) * 100 if total_raw_comments > 0 else 0
        metrics.append(DataQualityMetric(
            metric_name="Duplicate Rate",
            value=duplicate_rate,
            notes=f"Removed {total_raw_comments - cleaned_comments} duplicates from {total_raw_comments} raw records."
        ))
        
        # Missing Fields
        missing_rate = (missing_fields_count / total_fields_checked) * 100 if total_fields_checked > 0 else 0
        metrics.append(DataQualityMetric(
            metric_name="Missing Fields Rate",
            value=missing_rate,
            notes=f"Found {missing_fields_count} empty fields out of {total_fields_checked} total fields checked."
        ))
        
        # Total Records
        metrics.append(DataQualityMetric(
            metric_name="Total Cleaned Comments",
            value=cleaned_comments,
            notes="Final usable comment records."
        ))
        
        return metrics

    def analyze_missing_fields(self, projects: List[KickstarterProject]) -> Dict[str, int]:
        missing = 0
        total = 0
        for p in projects:
            fields = p.model_dump()
            for k, v in fields.items():
                total += 1
                if v is None or v == "" or (isinstance(v, list) and len(v) == 0):
                    missing += 1
        return {"missing": missing, "total": total}
