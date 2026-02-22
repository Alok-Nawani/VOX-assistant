from .base_skill import BaseSkill
from ..tools.file_manager import FileManager
from typing import Dict, Any

class FileManagementSkill(BaseSkill):
    """Standardized skill for managing files and directories"""
    
    def __init__(self):
        super().__init__("file_management")
        self.file_manager = FileManager()
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("raw_text", "").lower()
        intent = params.get("intent", "")
        
        if any(word in text for word in ["list", "show files", "what's in"]):
            return await self._handle_list(text)
        elif "search" in text or "find" in text:
            return await self._handle_search(text)
        elif "move" in text:
            return await self._handle_move(text)
        elif "delete" in text or "remove" in text:
            return await self._handle_delete(text)
            
        return {"success": False, "message": "I'm not sure what you want to do with those files, Alok."}

    async def _handle_list(self, text: str) -> Dict[str, Any]:
        # Simple extraction for "list files in [path]"
        path = "."
        if "in" in text:
            path = text.split("in")[-1].strip()
        
        try:
            items = self.file_manager.list_directory(path)
            if not items:
                return {"success": True, "message": f"Looks like {path} is empty."}
            
            msg = f"In {path}, I found: " + ", ".join([item['name'] for item in items[:5]])
            if len(items) > 5:
                msg += f" and {len(items)-5} more."
            return {"success": True, "message": msg}
        except Exception as e:
            return {"success": False, "message": f"I couldn't list that directory: {str(e)}"}

    async def _handle_search(self, text: str) -> Dict[str, Any]:
        pattern = text.split("search for")[-1].strip() if "search for" in text else ""
        if not pattern:
            return {"success": False, "message": "What should I search for, Alok?"}
            
        results = self.file_manager.search_files(pattern)
        if not results:
            return {"success": True, "message": f"I couldn't find any files matching '{pattern}'."}
            
        return {"success": True, "message": f"Found {len(results)} matches. The top one is {results[0]['path']}."}

    async def _handle_move(self, text: str) -> Dict[str, Any]:
        # This would need more complex parsing
        return {"success": False, "message": "I can move files, but you'll need to be more specific about from where to where."}

    async def _handle_delete(self, text: str) -> Dict[str, Any]:
        return {"success": False, "message": "I'm hesitant to delete files without a clearer confirmation system. Safety first!"}
