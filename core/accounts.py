from core.database import query

def get_accounts(user_id, is_admin=False):
    """
    Fetch all accounts for a specific user.
    Admins see all accounts.
    """
    if is_admin:
        rows = query("SELECT id, name, type, notes, user_id FROM accounts ORDER BY name", fetchall=True)
    else:
        rows = query(
            "SELECT id, name, type, notes, user_id FROM accounts WHERE user_id = ? ORDER BY name",
            (user_id,),
            fetchall=True
        )
    return [dict(r) for r in rows] if rows else []


def add_account(name, atype, notes='', user_id=None):
    """
    Add a new account for this user.
    """
    query(
        "INSERT INTO accounts (name, type, notes, user_id) VALUES (?, ?, ?, ?)",
        (name, atype, notes, user_id),
        commit=True
    )


def update_account(account_id, name=None, atype=None, notes=None, user_id=None, is_admin=False):
    """
    Update an account if owned by this user (or any user if admin).
    """
    parts = []
    params = []

    if name is not None:
        parts.append("name = ?"); params.append(name)
    if atype is not None:
        parts.append("type = ?"); params.append(atype)
    if notes is not None:
        parts.append("notes = ?"); params.append(notes)

    if not parts:
        return  # nothing to update

    if is_admin:
        q = "UPDATE accounts SET " + ", ".join(parts) + " WHERE id = ?"
        params.append(account_id)
    else:
        q = "UPDATE accounts SET " + ", ".join(parts) + " WHERE id = ? AND user_id = ?"
        params.extend([account_id, user_id])

    query(q, tuple(params), commit=True)


def delete_account(account_id, user_id=None, is_admin=False):
    """
    Delete account if owned by user (unless admin).
    Prevent deletion if linked transactions exist.
    """
    # Check for existing transactions
    r = query("SELECT COUNT(*) as c FROM transactions WHERE account_id = ?", (account_id,), fetchone=True)
    if r and r["c"] > 0:
        raise Exception("Cannot delete account with existing transactions.")

    if is_admin:
        query("DELETE FROM accounts WHERE id = ?", (account_id,), commit=True)
    else:
        query("DELETE FROM accounts WHERE id = ? AND user_id = ?", (account_id, user_id), commit=True)
