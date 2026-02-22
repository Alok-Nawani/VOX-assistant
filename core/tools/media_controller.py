import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Dict, List, Optional
import vlc
import logging
import os

class MediaController:
    """Controller for various media services"""
    
    def __init__(self):
        """Initialize media controller with various services"""
        self.spotify = None
        self.vlc_instance = None
        self.vlc_player = None
        self.current_service = None
        
    async def connect_spotify(self):
        """Connect to Spotify API"""
        try:
            scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
            self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
                scope=scope
            ))
            return True
        except Exception as e:
            logging.error(f"Error connecting to Spotify: {e}")
            return False
            
    def init_local_player(self):
        """Initialize VLC for local media playback"""
        try:
            self.vlc_instance = vlc.Instance()
            self.vlc_player = self.vlc_instance.media_player_new()
            return True
        except Exception as e:
            logging.error(f"Error initializing VLC player: {e}")
            return False
            
    async def play_media(self, query: str, service: str = "spotify") -> bool:
        """Play media from specified service
        
        Args:
            query: Search query or media URL
            service: Service to use (spotify, local, youtube)
        """
        try:
            self.current_service = service
            
            if service == "spotify":
                if not self.spotify:
                    if not await self.connect_spotify():
                        print("Vox System: Spotify not configured. Falling back to YouTube...")
                        return self._play_youtube_fallback(query)
                        
                # Search for track
                results = self.spotify.search(q=query, type="track", limit=1)
                if results and results["tracks"]["items"]:
                    track_uri = results["tracks"]["items"][0]["uri"]
                    try:
                        self.spotify.start_playback(uris=[track_uri])
                        return True
                    except:
                        return self._play_youtube_fallback(query)
                else:
                    return self._play_youtube_fallback(query)
                    
            elif service == "local":
                if not self.vlc_player:
                    if not self.init_local_player():
                        return False
                        
                media = self.vlc_instance.media_new(query)
                self.vlc_player.set_media(media)
                self.vlc_player.play()
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"Error playing media: {e}")
            return False
            
    async def pause(self) -> bool:
        """Pause current playback"""
        try:
            if self.current_service == "spotify":
                self.spotify.pause_playback()
            elif self.current_service == "local":
                self.vlc_player.pause()
            return True
        except Exception as e:
            logging.error(f"Error pausing playback: {e}")
            return False
            
    async def resume(self) -> bool:
        """Resume current playback"""
        try:
            if self.current_service == "spotify":
                self.spotify.start_playback()
            elif self.current_service == "local":
                self.vlc_player.play()
            return True
        except Exception as e:
            logging.error(f"Error resuming playback: {e}")
            return False
            
    async def next_track(self) -> bool:
        """Skip to next track"""
        try:
            if self.current_service == "spotify":
                self.spotify.next_track()
                return True
            return False
        except Exception as e:
            logging.error(f"Error skipping track: {e}")
            return False
            
    async def previous_track(self) -> bool:
        """Go back to previous track"""
        try:
            if self.current_service == "spotify":
                self.spotify.previous_track()
                return True
            return False
        except Exception as e:
            logging.error(f"Error going to previous track: {e}")
            return False
            
    async def set_volume(self, volume: int) -> bool:
        """Set playback volume (0-100)"""
        try:
            if self.current_service == "spotify":
                self.spotify.volume(volume)
            elif self.current_service == "local":
                self.vlc_player.audio_set_volume(volume)
            return True
        except Exception as e:
            logging.error(f"Error setting volume: {e}")
            return False
            
    def _play_youtube_fallback(self, query: str) -> bool:
        """Fallback to auto-play the first YouTube result in browser"""
        import webbrowser
        import urllib.parse
        import requests
        import re
        
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        try:
            # Simple attempt to find the first video ID via regex on the search page
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            response = requests.get(search_url, headers=headers, timeout=5)
            if response.status_code == 200:
                # Look for the first video ID in the page source
                video_ids = re.findall(r"\"videoRenderer\":\{\"videoId\":\"([^\"]+)\"", response.text)
                if video_ids:
                    video_url = f"https://www.youtube.com/watch?v={video_ids[0]}&autoplay=1"
                    print(f"Vox System: Found video {video_ids[0]}. Dispatching auto-play...")
                    webbrowser.open(video_url)
                    return True
        except Exception as e:
            print(f"Vox System: Auto-play extraction failed: {e}")
            
        # Last resort fallback to search page
        print("Vox System: Falling back to search results page.")
        webbrowser.open(search_url)
        return True

    async def get_current_track(self) -> Optional[Dict]:
        """Get information about currently playing track"""
        try:
            if self.current_service == "spotify":
                track = self.spotify.current_playback()
                if track and track.get("item"):
                    return {
                        "name": track["item"]["name"],
                        "artist": track["item"]["artists"][0]["name"],
                        "album": track["item"]["album"]["name"],
                        "duration": track["item"]["duration_ms"] // 1000,
                        "progress": track["progress_ms"] // 1000 if "progress_ms" in track else 0
                    }
            elif self.current_service == "local":
                if self.vlc_player.is_playing():
                    media = self.vlc_player.get_media()
                    return {
                        "name": media.get_mrl(),
                        "duration": self.vlc_player.get_length() // 1000,
                        "progress": self.vlc_player.get_time() // 1000
                    }
            return None
        except Exception as e:
            logging.error(f"Error getting current track: {e}")
            return None
