import sqlite3
from config import DATABASE_NAME

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_name TEXT NOT NULL,
        schedule_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def add_schedule(section_name: str, schedule_text: str):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO schedules (section_name, schedule_text) VALUES (?, ?)', 
                   (section_name, schedule_text))
    conn.commit()
    conn.close()

def get_schedules_count(section_name: str) -> int:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM schedules WHERE section_name = ?', (section_name,))
    result = cursor.fetchone()[0]
    conn.close()
    return result

def get_schedules_page(section_name: str, page: int, per_page: int = 1):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, schedule_text FROM schedules WHERE section_name = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
        (section_name, per_page, (page - 1) * per_page)
    )
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)

def delete_schedule(schedule_id: int):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
    conn.commit()
    conn.close()

# Инициализация БД при импорте
create_tables()