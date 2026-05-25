"""סקריפט חד-פעמי: מתקן טלפונים שאיבדו 0 מוביל בגיליון."""
import sys, io, json, tomllib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import gspread
from google.oauth2.service_account import Credentials

with open(".streamlit/secrets.toml", "rb") as f:
    cfg = tomllib.load(f)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(dict(cfg["gcp_service_account"]), scopes=SCOPES)
sh = gspread.authorize(creds).open_by_key(cfg["spreadsheet_id"])


def needs_fix(v):
    return isinstance(v, str) and v.isdigit() and len(v) == 9 and not v.startswith("0")


def fix_phones_in_obj(obj):
    """תיקון בתוך dict/list — מחזיר True אם משהו השתנה."""
    changed = [False]

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "phone" and needs_fix(v):
                    o[k] = "0" + v
                    changed[0] = True
                elif isinstance(v, (dict, list)):
                    walk(v)
        elif isinstance(o, list):
            for item in o:
                walk(item)

    walk(obj)
    return changed[0]


PHONE_COLS = {
    "bulk_deals":  ["organizer_phone", "business_phone"],
    "share_items": ["phone"],
    "gig_jobs":    ["phone"],
    "activities":  ["phone"],
}
JSON_COLS = ["participants_json", "volunteers_json", "comments_json", "carrier_json"]

for tab, cols in PHONE_COLS.items():
    ws = sh.worksheet(tab)
    rows = ws.get_all_values()
    if len(rows) < 2:
        continue
    headers = rows[0]
    updates = []

    for row_idx, row in enumerate(rows[1:], start=2):
        # תיקון עמודות טלפון רגילות
        for col_name in cols:
            if col_name in headers:
                col_idx = headers.index(col_name)
                if col_idx < len(row) and needs_fix(row[col_idx].strip()):
                    col_letter = gspread.utils.rowcol_to_a1(1, col_idx + 1).rstrip("1")
                    updates.append({
                        "range": f"{col_letter}{row_idx}",
                        "values": [["0" + row[col_idx].strip()]],
                    })

        # תיקון טלפונים בתוך JSON
        for col_name in JSON_COLS:
            if col_name not in headers:
                continue
            col_idx = headers.index(col_name)
            if col_idx >= len(row):
                continue
            val = row[col_idx].strip()
            if not val:
                continue
            try:
                data = json.loads(val)
            except Exception:
                continue
            if fix_phones_in_obj(data):
                col_letter = gspread.utils.rowcol_to_a1(1, col_idx + 1).rstrip("1")
                updates.append({
                    "range": f"{col_letter}{row_idx}",
                    "values": [[json.dumps(data, ensure_ascii=False)]],
                })

    if updates:
        # RAW — שומר את הערך בדיוק כמחרוזת, לא מפרש אותו כמספר
        ws.batch_update(updates, value_input_option="RAW")
        print(f"  ✅ {tab}: תוקנו {len(updates)} ערכים")
    else:
        print(f"  — {tab}: אין צורך בתיקון")

print("\n✨ סיום תיקון טלפונים")
