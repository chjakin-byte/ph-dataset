import yaml
import json
import os
from typing import Dict, Any, List
from app.models.config import PipelineConfig
from app.models.evidence import RawEvidence, KickstarterComment, KickstarterRewardTier, KickstarterProject
from app.collectors.kickstarter import KickstarterCollector
from app.analyzers.mapper import EvidenceMapper
from app.analyzers.deduplicator import Deduplicator
from app.analyzers.quality import QualityAnalyzer
from app.exporters.excel import ExcelExporter
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class PipelineRunner:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.deduplicator = Deduplicator()
        self.quality_analyzer = QualityAnalyzer()
        
    def _load_config(self) -> PipelineConfig:
        logger.info(f"Loading config from {self.config_path}")
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            return PipelineConfig(**data)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise

    def run(self):
        logger.info(f"Starting pipeline for product: {self.config.product_name}")
        
        try:
            # 1. Collect
            collector = KickstarterCollector()
            # For local test execution speed, we limit max_projects drastically if we just want a fast run, 
            # but default to config expectations if provided. Let's use 5 projects per keyword for testing.
            raw_data = collector.collect(self.config.target_keywords, max_projects=5)
            
            projects: List[KickstarterProject] = raw_data["projects"]
            comments: List[KickstarterComment] = raw_data["comments"]
            rewards: List[KickstarterRewardTier] = raw_data["rewards"]
            
            # Save Raw JSON
            os.makedirs("output/raw", exist_ok=True)
            with open("output/raw/projects.json", "w") as f:
                json.dump([p.model_dump(mode='json') for p in projects], f, indent=2)
            with open("output/raw/comments.json", "w") as f:
                json.dump([c.model_dump(mode='json') for c in comments], f, indent=2)
            with open("output/raw/rewards.json", "w") as f:
                json.dump([r.model_dump(mode='json') for r in rewards], f, indent=2)

            # 2. Quality & Cleaning (Deduplication)
            logger.info("Starting Deduplication and Quality Analysis")
            cleaned_comments, duplicate_comments_count = self.deduplicator.deduplicate_comments(comments)
            
            os.makedirs("output/cleaned", exist_ok=True)
            with open("output/cleaned/comments.json", "w") as f:
                json.dump([c.model_dump(mode='json') for c in cleaned_comments], f, indent=2)
                
            # Compute Quality Metrics
            expected_projects = len(self.config.target_keywords) * 5 
            missing_fields_info = self.quality_analyzer.analyze_missing_fields(projects)
            
            quality_metrics = self.quality_analyzer.generate_quality_metrics(
                raw_projects=len(projects),
                expected_projects=expected_projects,
                cleaned_comments=len(cleaned_comments),
                total_raw_comments=len(comments),
                missing_fields_count=missing_fields_info["missing"],
                total_fields_checked=missing_fields_info["total"]
            )
            
            # 3. Evidence Mapping (Transform comments into RawEvidence for the old pipeline flow)
            raw_evidence_list = []
            for c in cleaned_comments:
                score = self.quality_analyzer.calculate_evidence_score(
                    source_reliability=0.8, 
                    recency_days=(datetime.now() - c.comment_time).days, 
                    frequency=1
                )
                ev = RawEvidence(
                    source_platform="Kickstarter",
                    source_location="Comments Section",
                    timestamp=c.comment_time,
                    extracted_text=c.comment_text,
                    evidence_score=score,
                    frequency=1
                )
                raw_evidence_list.append(ev)
                
            mapper = EvidenceMapper()
            mapped_evidence = mapper.map_evidence(raw_evidence_list)
            
            # 4. Statistics
            stats = {
                "Total Projects": len(projects),
                "Total Raw Comments": len(comments),
                "Total Cleaned Comments": len(cleaned_comments),
                "Total Rewards": len(rewards),
                "Total FAQs": sum(p.faq_count for p in projects),
                "Total Updates": sum(p.update_count for p in projects)
            }
            
            # 5. Export
            exporter = ExcelExporter(self.config.output_path)
            exporter.export(raw_evidence_list, mapped_evidence, quality_metrics, stats)
            
            logger.info("Pipeline completed successfully.")
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise
