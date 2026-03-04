import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "daily_focus.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE task ADD COLUMN is_streak BOOLEAN DEFAULT 0")
    print("Successfully added is_streak column to task table")
except sqlite3.OperationalError as e:
    print(f"Error (might already exist): {e}")

conn.commit()
conn.close()
