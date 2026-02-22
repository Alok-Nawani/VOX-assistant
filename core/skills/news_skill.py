from typing import Dict, List, Optional, Any
from .base_skill import BaseSkill
from ..tools.news_service import NewsService
import logging

class NewsSkill(BaseSkill):
    """Skill for news and information"""
    
    def __init__(self):
        super().__init__("news")
        self.news_service = NewsService()
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("raw_text", "").lower()
        intent = params.get("intent", "")
        entities = params.get("entities", {})
        
        try:
            if any(word in text for word in ["headlines", "news", "what's happening"]):
                return await self._handle_headlines(text, entities)
            elif "search" in text or "about" in text:
                return await self._handle_search(text, entities)
            
            return {"success": False, "message": "I can catch you up on the news, Alok. Just ask for headlines or a specific topic."}
        except Exception as e:
            logging.error(f"News skill error: {e}")
            return {"success": False, "message": "I'm having some trouble reaching the news desk right now."}

    async def _handle_headlines(self, text: str, entities: Dict) -> Dict[str, Any]:
        articles = await self.news_service.get_top_headlines(limit=3)
        if not articles:
            return {"success": True, "message": "The news cycle seems a bit quiet right now, Alok."}
            
        msg = "Alright, here's what's making headlines: "
        for article in articles:
            msg += f"{article['title']}. "
            
        return {"success": True, "message": msg}

    async def _handle_search(self, text: str, entities: Dict) -> Dict[str, Any]:
        query = text.split("news about")[-1].strip() if "news about" in text else ""
        if not query:
            return {"success": False, "message": "What topic should I look for news on, Alok?"}
            
        articles = await self.news_service.search_news(query, limit=3)
        if not articles:
            return {"success": True, "message": f"I couldn't find any recent news on '{query}'."}
            
        return {"success": True, "message": f"Found a few things about '{query}'. For example: {articles[0]['title']}."}
