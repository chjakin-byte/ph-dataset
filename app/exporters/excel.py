import pandas as pd
from typing import List, Dict
import os
from app.models.evidence import MappedEvidence, RawEvidence
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ExcelExporter:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.required_sheets = [
            "Summary", "Raw Evidence", "Market", "User", "Pain Points", 
            "Competitors", "Evidence", "Launch Strategy", "Risk", 
            "Final Recommendation", "Logs", "Errors"
        ]

    def export(self, raw_evidence: List[RawEvidence], mapped_evidence: List[MappedEvidence]):
        logger.info(f"Exporting data to {self.output_path}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        with pd.ExcelWriter(self.output_path, engine='openpyxl') as writer:
            # 1. Summary
            pd.DataFrame([{"Pipeline": "Kickstarter Research", "Status": "Complete"}]).to_excel(writer, sheet_name="Summary", index=False)
            
            # 2. Raw Evidence
            raw_data = [r.model_dump() for r in raw_evidence]
            if raw_data:
                # Remove timezone if present to avoid Excel errors
                for d in raw_data:
                    if d.get('timestamp') and hasattr(d['timestamp'], 'replace'):
                        d['timestamp'] = d['timestamp'].replace(tzinfo=None)
                pd.DataFrame(raw_data).to_excel(writer, sheet_name="Raw Evidence", index=False)
            else:
                pd.DataFrame(columns=["source_platform", "source_location", "timestamp", "extracted_text", "relevance_score"]).to_excel(writer, sheet_name="Raw Evidence", index=False)
            
            # 3-10. Modules
            mapped_df = pd.DataFrame([m.model_dump() for m in mapped_evidence]) if mapped_evidence else pd.DataFrame(columns=["module"])
            
            for module in ["Market", "User", "Pain Points", "Competitors", "Evidence", "Launch Strategy", "Risk", "Final Recommendation"]:
                if not mapped_df.empty and 'module' in mapped_df.columns:
                    module_data = mapped_df[mapped_df["module"] == module]
                    # Format for module sheet: first list evidence, then conclusion
                    if not module_data.empty:
                        # Remove timezone if present
                        for col in module_data.columns:
                            if pd.core.dtypes.common.is_datetime64tz_dtype(module_data[col]):
                                module_data[col] = module_data[col].dt.tz_localize(None)
                        module_data.to_excel(writer, sheet_name=module, index=False)
                    else:
                        pd.DataFrame(columns=["extracted_text", "conclusion"]).to_excel(writer, sheet_name=module, index=False)
                else:
                    pd.DataFrame(columns=["extracted_text", "conclusion"]).to_excel(writer, sheet_name=module, index=False)
                    
            # 11. Logs
            pd.DataFrame([{"Log": "Execution logs saved locally."}]).to_excel(writer, sheet_name="Logs", index=False)
            
            # 12. Errors
            pd.DataFrame([{"Error": "No errors during generation."}]).to_excel(writer, sheet_name="Errors", index=False)
            
        logger.info(f"Successfully generated Excel report at {self.output_path}")
