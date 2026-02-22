import os
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging

class NewsService:
    """Service for fetching news and information"""
    
    def __init__(self):
        """Initialize news service with API keys"""
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.sports_api_key = os.getenv("SPORTS_API_KEY")
        
    async def get_top_headlines(self, category: str = None, 
                              country: str = "us", limit: int = 5) -> List[Dict]:
        """Get top news headlines
        
        Args:
            category: News category (business, tech, sports, etc.)
            country: Country code
            limit: Maximum number of articles
        """
        try:
            if not self.newsapi_key:
                raise ValueError("NewsAPI key not configured")
                
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": self.newsapi_key,
                "country": country,
                "pageSize": limit
            }
            
            if category:
                params["category"] = category
                
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return []
                        
                    data = await response.json()
                    articles = []
                    
                    for article in data.get("articles", []):
                        articles.append({
                            "title": article["title"],
                            "description": article.get("description", ""),
                            "source": article["source"]["name"],
                            "url": article["url"],
                            "published": article["publishedAt"]
                        })
                        
                    return articles
                    
        except Exception as e:
            logging.error(f"Error getting news headlines: {e}")
            return []
            
    async def search_news(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for news articles
        
        Args:
            query: Search query
            limit: Maximum number of articles
        """
        try:
            if not self.newsapi_key:
                raise ValueError("NewsAPI key not configured")
                
            url = "https://newsapi.org/v2/everything"
            params = {
                "apiKey": self.newsapi_key,
                "q": query,
                "pageSize": limit,
                "sortBy": "relevancy"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return []
                        
                    data = await response.json()
                    articles = []
                    
                    for article in data.get("articles", []):
                        articles.append({
                            "title": article["title"],
                            "description": article.get("description", ""),
                            "source": article["source"]["name"],
                            "url": article["url"],
                            "published": article["publishedAt"]
                        })
                        
                    return articles
                    
        except Exception as e:
            logging.error(f"Error searching news: {e}")
            return []
            
    async def get_sports_scores(self, sport: str = None) -> List[Dict]:
        """Get sports scores and results
        
        Args:
            sport: Sport type (football, basketball, etc.)
        """
        try:
            if not self.sports_api_key:
                raise ValueError("Sports API key not configured")
                
            # Using ESPN API for sports scores
            url = "https://api.espn.com/v1/sports"
            if sport:
                url += f"/{sport}/scores"
                
            params = {
                "apikey": self.sports_api_key,
                "limit": 5
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return []
                        
                    data = await response.json()
                    games = []
                    
                    for event in data.get("events", []):
                        game = {
                            "sport": event["sport"],
                            "status": event["status"],
                            "home_team": event["competitions"][0]["competitors"][0]["team"]["name"],
                            "away_team": event["competitions"][0]["competitors"][1]["team"]["name"],
                            "home_score": event["competitions"][0]["competitors"][0]["score"],
                            "away_score": event["competitions"][0]["competitors"][1]["score"],
                            "time": event.get("date")
                        }
                        games.append(game)
                        
                    return games
                    
        except Exception as e:
            logging.error(f"Error getting sports scores: {e}")
            return []
            
    def format_article(self, article: Dict) -> str:
        """Format a news article for speech output"""
        try:
            published = datetime.fromisoformat(
                article["published"].replace("Z", "+00:00"))
            time_str = published.strftime("%I:%M %p")
            
            return (
                f"{article['title']}\n"
                f"From {article['source']} at {time_str}\n"
                f"{article['description']}\n"
            )
        except Exception as e:
            logging.error(f"Error formatting article: {e}")
            return ""
            
    def format_game(self, game: Dict) -> str:
        """Format a sports game for speech output"""
        try:
            return (
                f"{game['sport'].title()}: "
                f"{game['home_team']} {game['home_score']} - "
                f"{game['away_team']} {game['away_score']}\n"
                f"Status: {game['status']}\n"
            )
        except Exception as e:
            logging.error(f"Error formatting game: {e}")
            return ""
