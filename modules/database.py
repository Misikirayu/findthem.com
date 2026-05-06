import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'history.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Performance tuning for SQLite
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=NORMAL')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            url TEXT NOT NULL,
            match_score INTEGER,
            status TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            nickname TEXT,
            target_user TEXT NOT NULL,
            video_id TEXT,
            text TEXT NOT NULL,
            sticker_url TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Unique index to prevent duplicate comments
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_comment_unique ON comments (username, text, video_id)')
    conn.commit()
    conn.close()

def add_comment(username, nickname, target_user, text, sticker_url=None, video_id=None):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20)
        c = conn.cursor()
        # Use INSERT OR IGNORE to prevent duplicates based on our unique index
        c.execute('''
            INSERT OR IGNORE INTO comments (username, nickname, target_user, text, sticker_url, video_id, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, nickname, target_user, text, sticker_url, video_id, datetime.now()))
        new_id = c.lastrowid
        conn.commit()
        conn.close()
        return new_id
    except Exception as e:
        print(f"Database Error in add_comment: {e}")
        return None

def get_comments(target_user=None, limit=100, offset=0):
    """Fetch comments with pagination support."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if target_user:
        c.execute(
            'SELECT id, username, nickname, text, sticker_url, video_id FROM comments WHERE target_user = ? ORDER BY fetched_at DESC LIMIT ? OFFSET ?',
            (target_user, limit, offset)
        )
    else:
        c.execute(
            'SELECT id, username, nickname, text, sticker_url, video_id FROM comments ORDER BY fetched_at DESC LIMIT ? OFFSET ?',
            (limit, offset)
        )
    rows = c.fetchall()
    conn.close()
    return [{"id_db": r[0], "user": r[1], "nickname": r[2], "text": r[3], "sticker_url": r[4], "video_id": r[5]} for r in rows]

def get_comment_count(target_user=None):
    """Get total number of comments, optionally filtered by target user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if target_user:
        c.execute('SELECT COUNT(*) FROM comments WHERE target_user = ?', (target_user,))
    else:
        c.execute('SELECT COUNT(*) FROM comments')
    count = c.fetchone()[0]
    conn.close()
    return count

def add_application(job_title, company, url, match_score, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO applications (job_title, company, url, match_score, status, applied_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (job_title, company, url, match_score, status, datetime.now()))
    conn.commit()
    conn.close()

def get_applications():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM applications ORDER BY applied_at DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def has_applied(url, company):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM applications WHERE url = ? OR company = ?', (url, company))
    row = c.fetchone()
    conn.close()
    return row is not None
