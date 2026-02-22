from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSkill(ABC):
    """Base class for all assistant skills"""
    
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill with given parameters
        
        Args:
            params: Dictionary of parameters (intent, entities, raw_text)
            
        Returns:
            Dictionary containing:
                - success: bool
                - message: str (to be spoken)
                - data: dict (optional raw data)
        """
        pass
