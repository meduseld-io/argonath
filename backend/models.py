"""
Argonath Database Models
SQLite-backed user accounts and activity logging.
"""

import sqlite3
import os
import hashlib
import hmac
import secrets
from datetime import datetime

from config import DATABASE_PATH, DATA_DIR


def get_db():
    """Get a database connection"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    """Hash a password with a random salt"""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"


def verify_password(password, password_hash):
    """Verify a password against its hash"""
    try:
        salt, hashed = password_hash.split(":")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(check.hex(), hashed)
    except Exception:
        return False


def create_user(username, password, role="viewer"):
    """Create a new user. Returns user dict or None if username taken."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role),
        )
        conn.commit()
        user = conn.execute(
            "SELECT id, username, role, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(user) if user else None
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(username, password):
    """Authenticate a user. Returns user dict or None."""
    conn = get_db()
    user = conn.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()

    if user and verify_password(password, user["password_hash"]):
        # Update last login
        conn = get_db()
        conn.execute(
            "UPDATE users SET last_login = datetime('now') WHERE id = ?", (user["id"],)
        )
        conn.commit()
        conn.close()
        return {"id": user["id"], "username": user["username"], "role": user["role"]}

    return None


def get_user_by_id(user_id):
    """Get a user by ID"""
    conn = get_db()
    user = conn.execute(
        "SELECT id, username, role, created_at, last_login FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_all_users():
    """Get all users (for admin panel)"""
    conn = get_db()
    users = conn.execute(
        "SELECT id, username, role, created_at, last_login FROM users"
    ).fetchall()
    conn.close()
    return [dict(u) for u in users]


def user_count():
    """Get total number of users"""
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


def update_user_role(user_id, new_role):
    """Update a user's role"""
    conn = get_db()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    """Delete a user"""
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def log_activity(user_id, action):
    """Log an activity"""
    conn = get_db()
    conn.execute(
        "INSERT INTO activity_log (user_id, action) VALUES (?, ?)",
        (user_id, action),
    )
    conn.commit()
    conn.close()


def get_activity_log(limit=50):
    """Get recent activity"""
    conn = get_db()
    rows = conn.execute("""
        SELECT a.id, a.action, a.timestamp, u.username
        FROM activity_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
