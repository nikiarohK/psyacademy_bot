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
        details_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def add_schedule(section_name: str, schedule_text: str, details_text: str = None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO schedules (section_name, schedule_text, details_text)
        VALUES (?, ?, ?)
    ''', (section_name, schedule_text, details_text))
    conn.commit()
    conn.close()

def update_schedule_details(schedule_id: int, details_text: str):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE schedules SET details_text = ?
        WHERE id = ?
    ''', (details_text, schedule_id))
    conn.commit()
    conn.close()

def get_schedules(section_name: str) -> list:
    """Получаем все расписания для раздела, отсортированные по дате"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, schedule_text, details_text FROM schedules 
        WHERE section_name = ?
        ORDER BY created_at DESC
    ''', (section_name,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_schedule_by_id(schedule_id: int) -> tuple:
    """Получаем конкретное расписание по ID"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT schedule_text, details_text FROM schedules 
        WHERE id = ?
    ''', (schedule_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def delete_schedule(schedule_id: int):
    """Удаляем расписание по ID"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
    conn.commit()
    conn.close()
    
def delete_schedule_by_id(schedule_id: int):
    """Удаляет расписание по его ID"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
    conn.commit()
    conn.close()

def get_all_schedules():
    """Получает все расписания из базы"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, section_name, schedule_text FROM schedules ORDER BY created_at DESC')
    results = cursor.fetchall()
    conn.close()
    return results

create_tables()