from datetime import datetime
import uuid

MONTHS = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
]

def month_name_from_index(i):
    return MONTHS[i-1]

def today_iso():
    return datetime.utcnow().isoformat()

def gen_uuid():
    return str(uuid.uuid4())
