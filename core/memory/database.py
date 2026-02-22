import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .schema import SCHEMA

@dataclass
class Reminder:
    id: Optional[int]
    title: str
    description: Optional[str]
    due_at: datetime
    remind_at: Optional[datetime]
    status: str = "pending"
    priority: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DatabaseManager:
    def __init__(self, db_path: str = "data/memory.db"):
        """Initialize database connection and ensure schema exists"""
        self.db_path = db_path
        self._ensure_db_exists()
        
    def _ensure_db_exists(self):
        """Create database and tables if they don't exist"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)
            
    def _row_to_reminder(self, row: tuple) -> Reminder:
        """Convert database row to Reminder object"""
        return Reminder(
            id=row[0],
            title=row[1],
            description=row[2],
            due_at=datetime.fromisoformat(row[3]),
            remind_at=datetime.fromisoformat(row[4]) if row[4] else None,
            status=row[5],
            priority=row[6],
            created_at=datetime.fromisoformat(row[7]) if row[7] else None,
            updated_at=datetime.fromisoformat(row[8]) if row[8] else None
        )
        
    def add_reminder(self, reminder: Reminder) -> int:
        """Add a new reminder and return its ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reminders (
                    title, description, due_at, remind_at, 
                    status, priority
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                reminder.title,
                reminder.description,
                reminder.due_at.isoformat(),
                reminder.remind_at.isoformat() if reminder.remind_at else None,
                reminder.status,
                reminder.priority
            ))
            return cursor.lastrowid
            
    def get_reminder(self, reminder_id: int) -> Optional[Reminder]:
        """Get a reminder by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, due_at, remind_at,
                       status, priority, created_at, updated_at
                FROM reminders WHERE id = ?
            """, (reminder_id,))
            
            row = cursor.fetchone()
            return self._row_to_reminder(row) if row else None
            
    def get_pending_reminders(self, limit: int = 10) -> List[Reminder]:
        """Get pending reminders ordered by due date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, due_at, remind_at,
                       status, priority, created_at, updated_at
                FROM reminders 
                WHERE status = 'pending'
                ORDER BY due_at ASC
                LIMIT ?
            """, (limit,))
            
            return [self._row_to_reminder(row) for row in cursor.fetchall()]
            
    def get_due_reminders(self) -> List[Reminder]:
        """Get reminders that are due for notification"""
        now = datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, due_at, remind_at,
                       status, priority, created_at, updated_at
                FROM reminders 
                WHERE status = 'pending'
                AND remind_at <= ?
            """, (now.isoformat(),))
            
            return [self._row_to_reminder(row) for row in cursor.fetchall()]
            
    def update_reminder(self, reminder: Reminder) -> bool:
        """Update an existing reminder"""
        if not reminder.id:
            return False
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reminders SET
                    title = ?,
                    description = ?,
                    due_at = ?,
                    remind_at = ?,
                    status = ?,
                    priority = ?
                WHERE id = ?
            """, (
                reminder.title,
                reminder.description,
                reminder.due_at.isoformat(),
                reminder.remind_at.isoformat() if reminder.remind_at else None,
                reminder.status,
                reminder.priority,
                reminder.id
            ))
            return cursor.rowcount > 0
            
    def mark_reminder_complete(self, reminder_id: int) -> bool:
        """Mark a reminder as completed"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reminders SET status = 'completed'
                WHERE id = ?
            """, (reminder_id,))
            return cursor.rowcount > 0
            
    def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            return cursor.rowcount > 0
            
    def cleanup_old_reminders(self, days: int = 30) -> int:
        """Clean up completed reminders older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM reminders 
                WHERE status = 'completed'
                AND updated_at < ?
            """, (cutoff.isoformat(),))
            return cursor.rowcount
