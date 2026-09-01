import sqlite3
from datetime import datetime, timedelta
import secrets

def init_db():
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()

    # Users table with verification fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_verified BOOLEAN DEFAULT 0,
            verification_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # API keys table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            plan TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Usage logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (key_id) REFERENCES api_keys (id)
        )
    """)

    conn.commit()
    conn.close()

def generate_api_key(plan: str) -> str:
    prefixes = {
        "Free": "QR_Free",
        "Pro": "QR_Pro",
        "Enterprise": "QR_Ent"
    }
    prefix = prefixes.get(plan, "QR_Free")
    random_part = secrets.token_urlsafe(24)
    return f"{prefix}_{random_part}"

def create_user(email: str, verification_token: str):
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, verification_token) VALUES (?, ?)",
            (email, verification_token)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_user_by_email(email: str):
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, is_verified, verification_token, created_at FROM users WHERE email = ?",
        (email,)
    )
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_by_token(token: str):
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email FROM users WHERE verification_token = ? AND is_verified = 0",
        (token,)
    )
    result = cursor.fetchone()
    conn.close()
    return result

def verify_user(user_id: int):
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET is_verified = 1, verification_token = NULL WHERE id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()

def create_api_key(user_id: int, plan: str) -> str:
    key = generate_api_key(plan)
    expires_at = datetime.now().replace(microsecond=0) + timedelta(days=30)
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO api_keys (key, user_id, plan, expires_at)
        VALUES (?, ?, ?, ?)
    """, (key, user_id, plan, expires_at))
    conn.commit()
    conn.close()
    return key

def get_key_info(api_key: str):
    """Get key details from the database"""
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT api_keys.id, api_keys.key, api_keys.user_id, api_keys.plan, 
               api_keys.is_active, api_keys.expires_at, users.is_verified
        FROM api_keys
        JOIN users ON api_keys.user_id = users.id
        WHERE api_keys.key = ?
    """, (api_key,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return None

    key_id, key, user_id, plan, is_active, expires_at, is_verified = result

    # Check if user is verified
    if not is_verified:
        return {"error": "Please verify your email before using this API key"}

    if expires_at:
        expires_at_date = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expires_at_date:
            return {"error": "Key expired"}

    if not is_active:
        return {"error": "Key inactive"}

    return {
        "id": key_id,
        "user_id": user_id,
        "plan": plan,
        "is_active": is_active
    }

def get_api_key_by_user_id(user_id: int):
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT key, plan, expires_at
        FROM api_keys
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "key": result[0],
            "plan": result[1],
            "expires_at": result[2],
        }
    return None

def log_usage(key_id: int, endpoint: str):
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usage_logs (key_id, endpoint)
        VALUES (?, ?)
    """, (key_id, endpoint))
    conn.commit()
    conn.close()

def get_today_usage(key_id: int) -> int:
    conn = sqlite3.connect("QR_codes.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM usage_logs
        WHERE key_id = ? AND date(requested_at) = date('now')
    """, (key_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count