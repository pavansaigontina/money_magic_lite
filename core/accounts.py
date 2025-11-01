from core.database import query

def get_accounts():
    rows = query("SELECT id,name,type,notes FROM accounts ORDER BY name", fetchall=True)
    return [dict(r) for r in rows] if rows else []

def add_account(name, atype, notes=''):
    query("INSERT INTO accounts (name,type,notes) VALUES (?,?,?)", (name, atype, notes), commit=True)

def update_account(account_id, name=None, atype=None, notes=None):
    parts = []
    params = []
    if name is not None:
        parts.append("name = ?"); params.append(name)
    if atype is not None:
        parts.append("type = ?"); params.append(atype)
    if notes is not None:
        parts.append("notes = ?"); params.append(notes)
    params.append(account_id)
    q = "UPDATE accounts SET " + ", ".join(parts) + " WHERE id = ?"
    query(q, tuple(params), commit=True)

def delete_account(account_id):
    r = query("SELECT COUNT(*) as c FROM transactions WHERE account_id = ?", (account_id,), fetchone=True)
    if r and r["c"] > 0:
        raise Exception("Cannot delete account with existing transactions.")
    query("DELETE FROM accounts WHERE id = ?", (account_id,), commit=True)
