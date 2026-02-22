import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class MemoryManager:
    """Manages Vox's long-term facts and short-term conversational context"""
    
    def __init__(self, db_path: str = "vox_assistant/data/memory/vox_memory.db"):
        self.db_path = db_path
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
                created_at TIMESTAMP
            )
        ''')
        
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

    def create_user(self, username: str, password_hash: str) -> int:
        """Create a new user and return their ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, created_at)
                VALUES (?, ?, ?)
            ''', (username, password_hash, datetime.now().isoformat()))
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return -1 # User already exists
        finally:
            conn.close()

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user details by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "username": row[1], "password_hash": row[2]}
        return None

    def store_fact(self, user_id: int, key: str, value: str):
        """Store or update a personal fact about the user"""
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT fact_key, fact_value FROM user_facts WHERE user_id = ?', (user_id,))
        facts = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return facts

    def log_interaction(self, user_id: int, role: str, content: str, image_url: Optional[str] = None):
        """Log a piece of the conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversation_logs (user_id, role, content, image_url, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, role, content, image_url, datetime.now().isoformat()))
        
        # Maintain only last 20 messages for short-term context window
        cursor.execute('''
            DELETE FROM conversation_logs 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM conversation_logs WHERE user_id = ? ORDER BY id DESC LIMIT 20
            )
        ''', (user_id, user_id))
        
        conn.commit()
        conn.close()

    def get_recent_context(self, user_id: int) -> List[Dict[str, str]]:
        """Retrieve recent conversation history for Gemini context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT role, content, image_url FROM conversation_logs WHERE user_id = ? ORDER BY id ASC', (user_id,))
        history = [{"role": row[0], "content": row[1], "image": row[2]} for row in cursor.fetchall()]
        conn.close()
        return history

    def search_facts(self, user_id: int, query: str) -> str:
        """Simple string match to find relevant facts based on user query"""
        facts = self.get_all_facts(user_id)
        relevant = []
        for k, v in facts.items():
            if k.lower() in query.lower() or any(word in query.lower() for word in k.split('_')):
                relevant.append(f"{k}: {v}")
        return "\n".join(relevant) if relevant else ""

class FactExtractor:
    """Uses AI to extract facts from conversation history"""
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        
    async def extract_and_store(self, user_id: int, conversation_text: str):
        """Analyze text for facts and update the DB using Gemini"""
        import google.generativeai as genai
        try:
            model = genai.GenerativeModel('gemini-flash-lite-latest')
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
