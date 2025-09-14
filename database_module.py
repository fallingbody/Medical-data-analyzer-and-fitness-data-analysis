import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'users.db')

def init_db():
    """Initialize database with proper schema"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Updated users table with profile_photo column
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT,
        phone TEXT,
        profile_photo TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create reports table with columns for feedback and verification
    c.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT NOT NULL,
        parameters TEXT,
        risks TEXT,
        plans TEXT,
        condition TEXT,
        feedback_condition TEXT,
        is_verified INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_report_by_id(report_id, user_id):
    """Get a single report by its ID, ensuring it belongs to the user."""
    conn = get_db_connection()
    report = conn.execute(
        'SELECT * FROM reports WHERE id = ? AND user_id = ?', (report_id, user_id)
    ).fetchone()
    conn.close()
    return report

def check_username_exists(username):
    """Check if a username already exists."""
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user is not None

def update_user_details(user_id, name, username, email, phone):
    """Update user's name, username, email, and phone."""
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE users SET name = ?, username = ?, email = ?, phone = ? WHERE id = ?',
            (name, username, email, phone, user_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # This will trigger if username or email is not unique
    finally:
        conn.close()

def update_profile_photo(user_id, photo_filename):
    """Update user's profile photo filename."""
    conn = get_db_connection()
    conn.execute('UPDATE users SET profile_photo = ? WHERE id = ?', (photo_filename, user_id))
    conn.commit()
    conn.close()

def delete_report_by_id(report_id, user_id):
    """Delete a specific report for a given user."""
    conn = get_db_connection()
    conn.execute('DELETE FROM reports WHERE id = ? AND user_id = ?', (report_id, user_id))
    conn.commit()
    conn.close()

def add_user(username, email, password, name, phone):
    """Add new user to database"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        password_hash = generate_password_hash(password)
        c.execute('''
        INSERT INTO users (username, email, password_hash, name, phone)
        VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password_hash, name, phone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_user(username, password):
    """Check user credentials"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        user = c.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    finally:
        conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        return True
    return False

def get_user_by_username(username):
    """Get user details by username"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        user = c.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    finally:
        conn.close()
    return dict(user) if user else None

def save_report(user_id, filename, parameters, risks, plans, condition):
    """Save report to database, auto-verify for retraining, and return the ID."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
        INSERT INTO reports (user_id, filename, parameters, risks, plans, condition, feedback_condition, is_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (user_id, filename, 
              json.dumps(parameters), 
              json.dumps(risks),
              json.dumps(plans),
              condition,
              condition)) # Save the AI's own prediction as the feedback
        conn.commit()
        # Return the ID of the newly inserted row
        return c.lastrowid
    finally:
        conn.close()

def get_reports_by_user_id(user_id):
    """Get all reports for a user"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        reports = c.execute('''
        SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,)).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in reports]