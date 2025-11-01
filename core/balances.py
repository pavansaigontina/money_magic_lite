from core.database import query

def get_opening(month, account_id):
    row = query("SELECT opening FROM balances WHERE month = ? AND account_id = ?", (month, account_id), fetchone=True)
    return float(row["opening"]) if row else 0.0

def set_opening(month, account_id, opening):
    row = query("SELECT id FROM balances WHERE month = ? AND account_id = ?", (month, account_id), fetchone=True)
    if row:
        query("UPDATE balances SET opening = ? WHERE month = ? AND account_id = ?", (float(opening), month, account_id), commit=True)
    else:
        query("INSERT INTO balances (month,account_id,opening) VALUES (?,?,?)", (month, account_id, float(opening)), commit=True)
