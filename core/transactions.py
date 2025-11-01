import uuid
from datetime import datetime
import pandas as pd
from core.database import query

def add_transaction(tx_date, account_id, category, description, tx_type, amount, user_id=None):
    tx_uuid = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    query(
        "INSERT INTO transactions (tx_uuid,date,account_id,category,description,type,amount,user_id,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (tx_uuid, tx_date.isoformat() if hasattr(tx_date,'isoformat') else str(tx_date),
         account_id, category, description, tx_type, float(amount), user_id, created_at),
        commit=True
    )
    return tx_uuid

def update_transaction_by_uuid(tx_uuid, updates: dict):
    parts=[]; params=[]
    for k,v in updates.items():
        parts.append(f"{k} = ?"); params.append(v)
    params.append(tx_uuid)
    q = f"UPDATE transactions SET {', '.join(parts)} WHERE tx_uuid = ?"
    query(q, tuple(params), commit=True)

def delete_transaction_by_uuid(tx_uuid):
    query("DELETE FROM transactions WHERE tx_uuid = ?", (tx_uuid,), commit=True)

def fetch_transactions(month_filter=None, start_date=None, end_date=None, account_ids=None, types=None):
    q = """SELECT t.tx_uuid as Transaction_ID, date(t.date) as Date,
                  a.name as Account, t.category as Category, t.description as Description,
                  t.type as Type, t.amount as Amount
           FROM transactions t
           LEFT JOIN accounts a ON t.account_id = a.id"""
    clauses=[]; params=[]
    if month_filter:
        months = ['January','February','March','April','May','June','July','August','September','October','November','December']
        mnum = f"{months.index(month_filter)+1:02d}"
        clauses.append("strftime('%m', t.date) = ?"); params.append(mnum)
    if start_date:
        clauses.append("date(t.date) >= date(?)"); params.append(start_date.isoformat())
    if end_date:
        clauses.append("date(t.date) <= date(?)"); params.append(end_date.isoformat())
    if account_ids:
        placeholders = ','.join(['?']*len(account_ids))
        clauses.append(f"t.account_id IN ({placeholders})"); params.extend(account_ids)
    if types and len(types)>0:
        placeholders = ','.join(['?']*len(types))
        clauses.append(f"t.type IN ({placeholders})"); params.extend(types)
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY date(t.date) DESC"
    rows = query(q, tuple(params), fetchall=True)
    return pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Transaction_ID","Date","Account","Category","Description","Type","Amount"])

