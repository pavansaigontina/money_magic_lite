from passlib.hash import pbkdf2_sha256
from datetime import datetime
from core.database import query

def create_user(username, password, display_name='', email=''):
    count_row = query("SELECT COUNT(*) as c FROM users", fetchone=True)
    count = count_row["c"] if count_row else 0
    is_admin = 1 if count == 0 else 0
    password_hash = pbkdf2_sha256.hash(password)
    created_at = datetime.utcnow().isoformat()
    try:
        query(
            "INSERT INTO users (username,password_hash,display_name,email,is_admin,created_at) VALUES (?,?,?,?,?,?)",
            (username, password_hash, display_name, email, is_admin, created_at),
            commit=True
        )
        return True, is_admin
    except Exception as e:
        return False, str(e)

def verify_user(username, password):
    row = query("SELECT * FROM users WHERE username = ?", (username,), fetchone=True)
    if not row:
        return False, "Invalid username or password"
    if pbkdf2_sha256.verify(password, row["password_hash"]):
        return True, dict(row)
    else:
        return False, "Invalid username or password"

def get_user_by_id(user_id):
    row = query("SELECT * FROM users WHERE id = ?", (user_id,), fetchone=True)
    return dict(row) if row else None

def update_user_details(user_id, display_name=None, email=None, new_password=None):
    if new_password:
        pw_hash = pbkdf2_sha256.hash(new_password)
        query("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, user_id), commit=True)
    if display_name is not None:
        query("UPDATE users SET display_name = ? WHERE id = ?", (display_name, user_id), commit=True)
    if email is not None:
        query("UPDATE users SET email = ? WHERE id = ?", (email, user_id), commit=True)
