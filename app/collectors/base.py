from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseCollector(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str:
        pass

    @abstractmethod
    def collect(self, keywords: List[str], max_projects: int) -> Dict[str, Any]:
        """
        Executes the collection logic for the specific platform.
        Returns a dictionary containing raw collected data structures.
        """
        pass