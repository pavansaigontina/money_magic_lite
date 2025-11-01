import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "money_magic.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT,
        email TEXT,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,
        notes TEXT
    );
    CREATE TABLE IF NOT EXISTS balances (
        id INTEGER PRIMARY KEY,
        month TEXT NOT NULL,
        account_id INTEGER NOT NULL,
        opening REAL DEFAULT 0,
        FOREIGN KEY(account_id) REFERENCES accounts(id)
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        tx_uuid TEXT UNIQUE NOT NULL,
        date TEXT NOT NULL,
        account_id INTEGER,
        category TEXT,
        description TEXT,
        type TEXT CHECK(type IN ('Expense','Income')) NOT NULL DEFAULT 'Expense',
        amount REAL NOT NULL DEFAULT 0,
        user_id INTEGER,
        created_at TEXT,
        FOREIGN KEY(account_id) REFERENCES accounts(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    conn.commit()
    conn.close()

def query(query, params=(), commit=False, fetchone=False, fetchall=False):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    result = None
    if fetchone:
        row = cur.fetchone()
        result = dict(row) if row else None
    if fetchall:
        rows = cur.fetchall()
        # convert to list of dicts so pandas has column names
        result = [dict(r) for r in rows] if rows else []
    if commit:
        conn.commit()
    conn.close()
    return result

