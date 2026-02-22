import threading
import time
import logging
from datetime import datetime
from typing import Callable, Dict, Any

from core.memory.database import DatabaseManager
from core.io.tts import speak

class ReminderMonitor:
    def __init__(self):
        """Initialize the reminder monitoring system"""
        self.db = DatabaseManager()
        self.running = False
        self.thread = None
        
    def _check_reminders(self):
        """Check for and notify about due reminders"""
        try:
            due_reminders = self.db.get_due_reminders()
            
            for reminder in due_reminders:
                # Speak the reminder
                message = f"Reminder: {reminder.title}"
                speak(message, interrupt=True)
                
                # Mark as notified by updating remind_at to None
                reminder.remind_at = None
                self.db.update_reminder(reminder)
                
        except Exception as e:
            logging.error(f"Error checking reminders: {e}")
            
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            self._check_reminders()
            time.sleep(60)  # Check every minute
            
    def start(self):
        """Start the reminder monitor"""
        if self.thread and self.thread.is_alive():
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logging.info("Reminder monitor started")
        
    def stop(self):
        """Stop the reminder monitor"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logging.info("Reminder monitor stopped")

# Global monitor instance
_monitor = None

def ensure_monitor_running():
    """Ensure the reminder monitor is running"""
    global _monitor
    if not _monitor:
        _monitor = ReminderMonitor()
        _monitor.start()

def stop_monitor():
    """Stop the reminder monitor"""
    global _monitor
    if _monitor:
        _monitor.stop()
        _monitor = None
