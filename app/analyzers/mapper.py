from typing import List
from app.models.evidence import RawEvidence, MappedEvidence
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class EvidenceMapper:
    def __init__(self):
        self.modules = [
            "Market", "User", "Pain Points", "Competitors", 
            "Evidence", "Launch Strategy", "Risk", "Final Recommendation"
        ]

    def map_evidence(self, raw_evidence_list: List[RawEvidence]) -> List[MappedEvidence]:
        logger.info(f"Mapping {len(raw_evidence_list)} raw evidence items to research modules.")
        mapped_list = []
        
        # Simple heuristic mapping for now.
        # Future enhancement: Use LLM/Model to classify
        for raw in raw_evidence_list:
            text_lower = raw.extracted_text.lower()
            assigned_module = "Evidence" # default
            
            if "market" in text_lower or "industry" in text_lower:
                assigned_module = "Market"
            elif "user" in text_lower or "customer" in text_lower or "backer" in text_lower:
                assigned_module = "User"
            elif "pain" in text_lower or "problem" in text_lower:
                assigned_module = "Pain Points"
            elif "competitor" in text_lower or "vs" in text_lower:
                assigned_module = "Competitors"
                
            mapped = MappedEvidence(
                **raw.model_dump(),
                module=assigned_module,
                conclusion=f"Conclusion based on: {raw.extracted_text[:50]}..."
            )
            mapped_list.append(mapped)
            
        logger.info(f"Successfully mapped {len(mapped_list)} items.")
        return mapped_list
