"""SQLite schema for reminders database"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    due_at TIMESTAMP NOT NULL,
    remind_at TIMESTAMP,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reminders_due_at ON reminders(due_at);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);

CREATE TABLE IF NOT EXISTS recurring_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reminder_id INTEGER NOT NULL,
    frequency TEXT NOT NULL,  -- daily, weekly, monthly, yearly
    interval INTEGER DEFAULT 1,
    days_of_week TEXT,  -- comma-separated: 0,1,2,3,4,5,6 (Sunday=0)
    day_of_month INTEGER,
    month INTEGER,
    until_date DATE,
    FOREIGN KEY (reminder_id) REFERENCES reminders(id) ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS update_reminder_timestamp
    AFTER UPDATE ON reminders
    FOR EACH ROW
    BEGIN
        UPDATE reminders SET updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.id;
    END;
"""
