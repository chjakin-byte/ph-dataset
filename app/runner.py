import yaml
import json
import os
from typing import Dict, Any
from app.models.config import PipelineConfig
from app.collectors.kickstarter import KickstarterCollector
from app.analyzers.mapper import EvidenceMapper
from app.exporters.excel import ExcelExporter
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class PipelineRunner:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        
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
            raw_evidence = collector.collect(self.config.target_keywords)
            
            # Save raw evidence as JSON
            os.makedirs("output/raw", exist_ok=True)
            with open("output/raw/evidence.json", "w") as f:
                json.dump([r.model_dump(mode='json') for r in raw_evidence], f, indent=2)
                
            # 2. Map/Analyze
            mapper = EvidenceMapper()
            mapped_evidence = mapper.map_evidence(raw_evidence)
            
            # 3. Export
            exporter = ExcelExporter(self.config.output_path)
            exporter.export(raw_evidence, mapped_evidence)
            
            logger.info("Pipeline completed successfully.")
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise
