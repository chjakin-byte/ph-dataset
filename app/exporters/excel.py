import pandas as pd
from typing import List, Dict, Any
import os
from app.models.evidence import MappedEvidence, RawEvidence, DataQualityMetric
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ExcelExporter:
    def __init__(self, output_path: str):
        self.output_path = output_path
        # Now 15 sheets
        self.required_sheets = [
            "Summary", "Raw Evidence", "Market", "User", "Pain Points", 
            "Competitors", "Evidence", "Launch Strategy", "Risk", 
            "Final Recommendation", "Signal Detection", "Signal Score", 
            "Data Quality", "Logs", "Errors"
        ]

    def _remove_timezone(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if pd.core.dtypes.common.is_datetime64tz_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)
        return df

    def export(self, raw_evidence: List[RawEvidence], mapped_evidence: List[MappedEvidence], 
               quality_metrics: List[DataQualityMetric], stats: Dict[str, Any]):
        logger.info(f"Exporting data to {self.output_path}")
        
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        with pd.ExcelWriter(self.output_path, engine='openpyxl') as writer:
            # 1. Summary (now with Stats)
            summary_data = [{"Pipeline": "Kickstarter Research", "Status": "Complete"}]
            summary_data[0].update(stats)
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
            
            # 2. Raw Evidence
            raw_data = [r.model_dump() for r in raw_evidence]
            if raw_data:
                df = pd.DataFrame(raw_data)
                for d in raw_data:
                    if d.get('timestamp') and hasattr(d['timestamp'], 'replace'):
                        d['timestamp'] = d['timestamp'].replace(tzinfo=None)
                df = pd.DataFrame(raw_data)
                df.to_excel(writer, sheet_name="Raw Evidence", index=False)
            else:
                pd.DataFrame(columns=["source_platform", "source_location", "timestamp", "extracted_text", "evidence_score", "frequency"]).to_excel(writer, sheet_name="Raw Evidence", index=False)
            
            # 3-10. 8 Core Modules
            mapped_df = pd.DataFrame([m.model_dump() for m in mapped_evidence]) if mapped_evidence else pd.DataFrame(columns=["module"])
            
            for module in ["Market", "User", "Pain Points", "Competitors", "Evidence", "Launch Strategy", "Risk", "Final Recommendation"]:
                if not mapped_df.empty and 'module' in mapped_df.columns:
                    module_data = mapped_df[mapped_df["module"] == module]
                    if not module_data.empty:
                        module_data = self._remove_timezone(module_data)
                        module_data.to_excel(writer, sheet_name=module, index=False)
                    else:
                        pd.DataFrame(columns=["extracted_text", "conclusion"]).to_excel(writer, sheet_name=module, index=False)
                else:
                    pd.DataFrame(columns=["extracted_text", "conclusion"]).to_excel(writer, sheet_name=module, index=False)
            
            # 11. Signal Detection (Placeholder for Phase 2)
            pd.DataFrame(columns=["signal_name", "signal_score", "evidence_references", "description"]).to_excel(writer, sheet_name="Signal Detection", index=False)
            
            # 12. Signal Score (Placeholder for Phase 2 - Replaced Opportunity Score)
            pd.DataFrame(columns=["signal_name", "signal_score", "evidence_references", "description"]).to_excel(writer, sheet_name="Signal Score", index=False)

            # 13. Data Quality
            dq_data = [q.model_dump() for q in quality_metrics]
            if dq_data:
                pd.DataFrame(dq_data).to_excel(writer, sheet_name="Data Quality", index=False)
            else:
                pd.DataFrame(columns=["metric_name", "value", "notes"]).to_excel(writer, sheet_name="Data Quality", index=False)

            # 14. Logs
            pd.DataFrame([{"Log": "Execution logs saved locally in output/logs/."}]).to_excel(writer, sheet_name="Logs", index=False)
            
            # 15. Errors
            pd.DataFrame([{"Error": "No errors recorded in this scope."}]).to_excel(writer, sheet_name="Errors", index=False)
            
        logger.info(f"Successfully generated Excel report at {self.output_path} with 15 sheets.")
