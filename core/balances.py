from core.database import query

def get_opening(month, account_id, user_id, is_admin=False):
    if is_admin:
        row = query(
            "SELECT opening FROM balances WHERE month = ? AND account_id = ? ORDER BY id DESC LIMIT 1",
            (month, account_id),
            fetchone=True,
        )
    else:
        row = query(
            "SELECT opening FROM balances WHERE month = ? AND account_id = ? AND user_id = ?",
            (month, account_id, user_id),
            fetchone=True,
        )
    return float(row["opening"]) if row else 0.0

def set_opening(month, account_id, opening, user_id):
    row = query(
        "SELECT id FROM balances WHERE month = ? AND account_id = ? AND user_id = ?",
        (month, account_id, user_id),
        fetchone=True,
    )
    if row:
        query(
            "UPDATE balances SET opening = ? WHERE month = ? AND account_id = ? AND user_id = ?",
            (float(opening), month, account_id, user_id),
            commit=True,
        )
    else:
        query(
            "INSERT INTO balances (month, account_id, opening, user_id) VALUES (?, ?, ?, ?)",
            (month, account_id, float(opening), user_id),
            commit=True,
        )
