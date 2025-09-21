import sqlite3
import json
from datetime import datetime

def init_db():
    conn = sqlite3.connect('habtebot.db')
    c = conn.cursor()
    
    # Table for job submissions - execute separately
    c.execute('''
        CREATE TABLE IF NOT EXISTS job_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            contact_info TEXT,
            status TEXT DEFAULT 'pending',
            submitted_at TIMESTAMP
        )
    ''')
    
    # Table for user CV data - execute separately
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_cvs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            headline TEXT,
            skills TEXT,
            experience TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_job_submission(user_id, title, description, contact_info):
    conn = sqlite3.connect('habtebot.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO job_submissions (user_id, title, description, contact_info, submitted_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, title, description, contact_info, datetime.now()))
    conn.commit()
    conn.close()

def add_cv_draft(user_id, full_name, headline, skills, experience):
    conn = sqlite3.connect('habtebot.db')
    c = conn.cursor()
    
    # Convert skills list to JSON string
    skills_json = json.dumps(skills)
    
    # Check if draft exists
    c.execute('SELECT id FROM user_cvs WHERE user_id = ? AND status = "draft"', (user_id,))
    draft = c.fetchone()
    
    if draft:
        # Update existing draft
        c.execute('''
            UPDATE user_cvs SET full_name=?, headline=?, skills=?, experience=?
            WHERE id=?
        ''', (full_name, headline, skills_json, experience, draft[0]))
    else:
        # Insert new draft
        c.execute('''
            INSERT INTO user_cvs (user_id, full_name, headline, skills, experience, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, full_name, headline, skills_json, experience, datetime.now()))
    
    conn.commit()
    conn.close()

# Initialize the database when this module is imported
init_db()