import sqlite3
from config import DATABASE_NAME

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_name TEXT NOT NULL UNIQUE,
        schedule_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def add_schedule(section_name: str, schedule_text: str):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO schedules (section_name, schedule_text)
        VALUES (?, ?)
    ''', (section_name, schedule_text))
    conn.commit()
    conn.close()

def get_latest_schedule(section_name: str) -> str:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT schedule_text FROM schedules 
        WHERE section_name = ?
        LIMIT 1
    ''', (section_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def delete_schedule(section_name: str):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM schedules WHERE section_name = ?', (section_name,))
    conn.commit()
    conn.close()

create_tables()