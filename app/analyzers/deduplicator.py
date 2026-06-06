from typing import List, Dict, Any, Tuple
from app.models.evidence import KickstarterComment, RawEvidence

class Deduplicator:
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def _jaccard_similarity(self, str1: str, str2: str) -> float:
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union

    def deduplicate_comments(self, comments: List[KickstarterComment]) -> Tuple[List[KickstarterComment], int]:
        """
        Deduplicates comments based on text similarity.
        Returns cleaned comments and the number of duplicates found.
        """
        cleaned = []
        duplicates = 0
        
        for comment in comments:
            is_duplicate = False
            for existing in cleaned:
                # We reuse like_count or add a frequency field if we want, 
                # but for KickstarterComment we can just drop exact or near-duplicate bot spam.
                if self._jaccard_similarity(comment.comment_text, existing.comment_text) >= self.similarity_threshold:
                    is_duplicate = True
                    duplicates += 1
                    break
            if not is_duplicate:
                cleaned.append(comment)
                
        return cleaned, duplicates

    def deduplicate_evidence(self, evidence_list: List[RawEvidence]) -> Tuple[List[RawEvidence], int]:
        cleaned = []
        duplicates = 0
        
        for ev in evidence_list:
            is_duplicate = False
            for existing in cleaned:
                if self._jaccard_similarity(ev.extracted_text, existing.extracted_text) >= self.similarity_threshold:
                    existing.frequency += 1
                    is_duplicate = True
                    duplicates += 1
                    break
            if not is_duplicate:
                cleaned.append(ev)
                
        return cleaned, duplicates
