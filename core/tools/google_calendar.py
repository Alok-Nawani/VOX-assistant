import os
import pickle
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging

# If modifying these scopes, delete the token file.
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]

class GoogleAuthManager:
    def __init__(self, credentials_path: str = "configs/google_credentials.json"):
        """Initialize Google Calendar API auth manager"""
        self.credentials_path = credentials_path
        self._ensure_paths()
        
    def _ensure_paths(self):
        """Ensure necessary directories exist"""
        Path("data/token").mkdir(parents=True, exist_ok=True)
        
    async def get_credentials(self, user_id: int) -> Optional[Credentials]:
        """Get valid Google credentials for a specific user"""
        creds = None
        token_path = f"data/token/google_token_{user_id}.pickle"
        
        # Load existing token if present
        if os.path.exists(token_path):
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logging.error(f"Error loading token for user {user_id}: {e}")
                
        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logging.error(f"Error refreshing token for user {user_id}: {e}")
                creds = None
                
        # Generate new token if none exists
        if not creds or not creds.valid:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    "Google credentials not found. System-wide setup required."
                )
                
            try:
                logging.info(f"Initiating Google OAuth local server for user {user_id}...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                
                # Tactical Patch: Ensure we get a refresh token for long-term survival
                flow.oauth2session.scope = SCOPES
                
                import asyncio
                creds = await asyncio.to_thread(
                    flow.run_local_server,
                    port=0,
                    open_browser=True,
                    timeout_seconds=300,
                    access_type='offline',
                    prompt='consent'
                )
                
                logging.info(f"Successfully obtained credentials for user {user_id}")
                
                # Save the credentials for this specific user
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                logging.error(f"Error getting new token for user {user_id}: {str(e)}")
                return None
                
        return creds

class CalendarAPI:
    def __init__(self):
        """Initialize Google Calendar API client"""
        self.auth_manager = GoogleAuthManager()
        self.services = {} # Store services per user
        
    async def _ensure_service(self, user_id: int):
        """Ensure calendar service is initialized for a specific user"""
        if user_id not in self.services:
            creds = await self.auth_manager.get_credentials(user_id)
            if not creds:
                raise Exception(f"Failed to get Google credentials for user {user_id}")
            self.services[user_id] = build('calendar', 'v3', credentials=creds)
            
    async def get_service(self, user_id: int):
        """Get the calendar service instance for a user"""
        await self._ensure_service(user_id)
        return self.services[user_id]
