import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import logging

class MemoryManager:
    """Manages Vox's long-term facts and short-term conversational context (Hybrid SQLite/Supabase)"""
    
    def __init__(self, db_path: str = "data/memory/vox_memory.db"):
        self.db_path = db_path
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        self.client: Optional[Client] = None
        
        if self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                logging.info("Vox Memory: Cloud Uplink Established (Supabase)")
            except Exception as e:
                logging.error(f"Vox Memory: Supabase Connection Failed: {e}")
        
        if not self.client:
            logging.info("Vox Memory: Operating in Local Mode (SQLite)")
            self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database with required tables and columns"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Create Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                full_name TEXT,
                avatar_url TEXT,
                created_at TIMESTAMP
            )
        ''')

        # Migration: Add full_name if missing
        try:
            cursor.execute("SELECT full_name FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")

        # Migration: Add avatar_url if missing
        try:
            cursor.execute("SELECT avatar_url FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        
        # 2. Handle migrations for existing tables (User Facts & Logs)
        # Create them if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_facts (
                user_id INTEGER,
                fact_key TEXT,
                fact_value TEXT,
                updated_at TIMESTAMP,
                PRIMARY KEY (user_id, fact_key)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                image_url TEXT,
                timestamp TIMESTAMP
            )
        ''')

        # Check for missing user_id column in existing table (Edge case for old DBs)
        try:
            cursor.execute("SELECT user_id FROM user_facts LIMIT 1")
        except sqlite3.OperationalError:
            print("Migrating memory database: Adding user_id to user_facts")
            # For user_facts, we need to drop and recreate since it's a primary key change
            cursor.execute("DROP TABLE IF EXISTS user_facts")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_facts (
                    user_id INTEGER,
                    fact_key TEXT,
                    fact_value TEXT,
                    updated_at TIMESTAMP,
                    PRIMARY KEY (user_id, fact_key)
                )
            ''')

        try:
            cursor.execute("SELECT user_id FROM conversation_logs LIMIT 1")
        except sqlite3.OperationalError:
            print("Migrating logs database: Adding user_id to conversation_logs")
            cursor.execute("ALTER TABLE conversation_logs ADD COLUMN user_id INTEGER DEFAULT 1")

        try:
            cursor.execute("SELECT image_url FROM conversation_logs LIMIT 1")
        except sqlite3.OperationalError:
            print("Migrating logs database: Adding image_url to conversation_logs")
            cursor.execute("ALTER TABLE conversation_logs ADD COLUMN image_url TEXT")
        
        conn.commit()
        conn.close()

    def create_user(self, username: str, password_hash: str, full_name: str = "") -> int:
        """Create a new user and return their ID"""
        if self.client:
            try:
                response = self.client.table("users").insert({
                    "username": username,
                    "password_hash": password_hash,
                    "full_name": full_name
                }).execute()
                return response.data[0]["id"]
            except Exception as e:
                logging.error(f"Supabase Create User Error: {e}")
                return -1
                
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, full_name, datetime.now().isoformat()))
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return -1 # User already exists
        finally:
            conn.close()

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user details by username"""
        if self.client:
            try:
                response = self.client.table("users").select("*").eq("username", username).execute()
                if response.data:
                    user = response.data[0]
                    return {"id": user["id"], "username": user["username"], "password_hash": user["password_hash"], "full_name": user["full_name"], "avatar_url": user["avatar_url"]}
                return None
            except Exception as e:
                logging.error(f"Supabase Get User Error: {e}")
                return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, full_name, avatar_url FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "username": row[1], "password_hash": row[2], "full_name": row[3], "avatar_url": row[4]}
        return None

    def update_user_avatar(self, user_id: int, avatar_url: str):
        """Update the user's profile picture"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET avatar_url = ? WHERE id = ?', (avatar_url, user_id))
        conn.commit()
        conn.close()

    def store_fact(self, user_id: int, key: str, value: str):
        """Store or update a personal fact about the user"""
        if self.client:
            try:
                self.client.table("user_facts").upsert({
                    "user_id": user_id,
                    "fact_key": key,
                    "fact_value": value,
                    "updated_at": datetime.now().isoformat()
                }).execute()
                return
            except Exception as e:
                logging.error(f"Supabase Store Fact Error: {e}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_facts (user_id, fact_key, fact_value, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, key, value, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_fact(self, user_id: int, key: str) -> Optional[str]:
        """Retrieve a specific fact"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT fact_value FROM user_facts WHERE user_id = ? AND fact_key = ?', (user_id, key))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_all_facts(self, user_id: int) -> Dict[str, str]:
        """Retrieve all known facts as a dictionary"""
        if self.client:
            try:
                response = self.client.table("user_facts").select("fact_key, fact_value").eq("user_id", user_id).execute()
                return {row["fact_key"]: row["fact_value"] for row in response.data}
            except Exception as e:
                logging.error(f"Supabase Get Facts Error: {e}")
                return {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT fact_key, fact_value FROM user_facts WHERE user_id = ?', (user_id,))
        facts = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return facts

    def log_interaction(self, user_id: int, role: str, content: str, image_url: Optional[str] = None):
        """Log a piece of the conversation"""
        if self.client:
            try:
                self.client.table("conversation_logs").insert({
                    "user_id": user_id,
                    "role": role,
                    "content": content,
                    "image_url": image_url
                }).execute()
                # Cloud doesn't strictly need rotation for now (managed by DB size)
                return
            except Exception as e:
                logging.error(f"Supabase Log Error: {e}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversation_logs (user_id, role, content, image_url, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, role, content, image_url, datetime.now().isoformat()))
        
        # Maintain only last 12 messages for faster processing
        cursor.execute('''
            DELETE FROM conversation_logs 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM conversation_logs WHERE user_id = ? ORDER BY id DESC LIMIT 12
            )
        ''', (user_id, user_id))
        
        conn.commit()
        conn.close()

    def get_recent_context(self, user_id: int) -> List[Dict[str, str]]:
        """Retrieve recent conversation history for Gemini context"""
        if self.client:
            try:
                response = self.client.table("conversation_logs").select("role, content, image_url").eq("user_id", user_id).order("id", desc=False).limit(12).execute()
                return [{"role": row["role"], "content": row["content"], "image": row["image_url"]} for row in response.data]
            except Exception as e:
                logging.error(f"Supabase Get History Error: {e}")
                return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT role, content, image_url FROM conversation_logs WHERE user_id = ? ORDER BY id ASC', (user_id,))
        history = [{"role": row[0], "content": row[1], "image": row[2]} for row in cursor.fetchall()]
        conn.close()
        return history

    def clear_history(self, user_id: int):
        """Delete all conversation logs for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM conversation_logs WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def search_facts(self, user_id: int, query: str) -> str:
        """Simple string match to find relevant facts based on user query"""
        facts = self.get_all_facts(user_id)
        relevant = []
        for k, v in facts.items():
            if k.lower() in query.lower() or any(word in query.lower() for word in k.split('_')):
                relevant.append(f"{k}: {v}")
        return "\n".join(relevant) if relevant else ""

    def store_alias(self, user_id: int, trigger: str, action: str):
        """Store a custom command alias"""
        self.store_fact(user_id, f"alias_{trigger.lower().strip()}", action)
        
    def get_aliases(self, user_id: int) -> Dict[str, str]:
        """Retrieve all custom aliases for the user"""
        facts = self.get_all_facts(user_id)
        return {k.replace('alias_', ''): v for k, v in facts.items() if k.startswith('alias_')}

class FactExtractor:
    """Uses AI to extract facts from conversation history"""
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        
    async def extract_and_store(self, user_id: int, conversation_text: str):
        """Analyze text for facts and update the DB using Gemini"""
        import google.generativeai as genai
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = (
                "You are the VOX Kernel Learning Module. "
                "Analyze this diagnostic interaction and identify any persistent user patterns, preferences, or environment variables "
                "specifically related to Alok.\n\n"
                "Data Stream:\n" + conversation_text + "\n\n"
                "Output ONLY a JSON array of pattern objects with 'key' (snake_case) and 'value'. "
                "Example: [{\"key\": \"priority_tool\", \"value\": \"VS Code\"}]\n"
                "If no new patterns identified, output []."
            )
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            # Handle potential markdown in LLM output
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].strip()
                
            facts = json.loads(text)
            for fact in facts:
                if 'key' in fact and 'value' in fact:
                    self.memory.store_fact(user_id, fact['key'], fact['value'])
                    print(f"Vox Memory: Learned {fact['key']} for User {user_id}")
        except Exception as e:
            print(f"Fact Extraction Failed: {e}")
