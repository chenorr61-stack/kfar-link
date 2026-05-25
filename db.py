"""
db.py — שכבת גישה ל-Google Sheets
=====================================
מודול יחיד שמחליף את st.session_state ככלי אחסון עבור Kfar-Link.

עיקרון: כל פעולת קריאה/כתיבה נעשית מול הגיליון. שדות מורכבים
(dict/list) מאוחסנים כ-JSON בתוך עמודת '…_json' כדי להתאים
למבנה טבלאי של גיליון.

פונקציות עזר:
    load_all()               — טעינת כל הנתונים (users, bulk_deals, …)
    upsert_user(name, phone) — רישום משתמש חדש / עדכון last_seen
    add_bulk_deal(deal)      — כתיבת עסקה חדשה
    update_bulk_deal(deal)   — עדכון עסקה קיימת (לפי id)
    delete_row(tab, id_)     — מחיקת שורה לפי id
    … (וכן הלאה לכל מודול)

כל הפונקציות משתמשות ב-@st.cache_resource לחיבור ו-TTL cache קצר
לקריאות כדי להפחית קריאות ל-Sheets API.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# עמודות שמכילות JSON מוטמע (dict/list)
JSON_COLS = {
    "bulk_deals": {"carrier_json", "participants_json", "comments_json"},
    "activities": {"participants_json", "volunteers_json"},
}

# מיפוי שמות שדות פנימיים → עמודות בגיליון (רק אלה ששונים)
# מבנה: (טאב, שדה_פנימי) -> שם_עמודה_בגיליון
INTERNAL_TO_SHEET = {
    ("bulk_deals", "carrier"): "carrier_json",
    ("bulk_deals", "participants"): "participants_json",
    ("bulk_deals", "comments"): "comments_json",
    ("activities", "participants"): "participants_json",
    ("activities", "volunteers"): "volunteers_json",
}

# הפוך — גיליון → פנימי
SHEET_TO_INTERNAL = {v: k[1] for k, v in INTERNAL_TO_SHEET.items()}


# ──────────────────────────────────────────────
# חיבור לגיליון
# ──────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _get_spreadsheet():
    """מחזיר אובייקט Spreadsheet מחובר — cached כדי לא לפתוח חיבור חדש בכל rerun."""
    svc_info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(svc_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["spreadsheet_id"])


def _ws(tab_name: str):
    """מחזיר worksheet (הגיליון הבודד) של טאב נתון."""
    return _get_spreadsheet().worksheet(tab_name)


# ──────────────────────────────────────────────
# המרה: שורה בגיליון ↔ dict פנימי
# ──────────────────────────────────────────────
def _row_to_dict(row: dict, tab_name: str) -> dict:
    """
    הופך שורה (dict של {col_name: value}) ל-dict פנימי:
    - מפרש עמודות _json חזרה ל-dict/list
    - ממפה שם עמודה חזרה לשם השדה הפנימי
    - ממיר מספרים מחרוזת ל-int/float כשאפשר (פרט לטלפונים/id)
    """
    # שדות שחייבים להישאר מחרוזת גם אם הם נראים כמו מספר
    # (טלפונים יכולים להתחיל ב-0 שייבלע בהמרה ל-int)
    STRING_ONLY_COLS = {
        "phone", "organizer_phone", "business_phone", "id",
        "event_time", "first_seen", "last_seen", "created_at",
        "target_date", "event_date",
    }

    out = {}
    for col, val in row.items():
        # המרה מ-col → internal name
        key = SHEET_TO_INTERNAL.get(col, col)

        # פענוח JSON
        if col in JSON_COLS.get(tab_name, set()):
            if not val:
                out[key] = [] if "participants" in col or "volunteers" in col or "comments" in col else None
            else:
                try:
                    out[key] = json.loads(val) if isinstance(val, str) else val
                except Exception:
                    out[key] = [] if "participants" in col or "volunteers" in col or "comments" in col else None
            continue

        # שדות שחייבים להישאר מחרוזת
        if col in STRING_ONLY_COLS:
            out[key] = str(val) if val not in (None, "") else None
            continue

        # gspread לפעמים כבר מחזיר int/float — מכבדים את זה
        if isinstance(val, (int, float)):
            out[key] = val
            continue

        # ניסיון המרה למספר רק למחרוזות
        if isinstance(val, str) and val.strip():
            try:
                if "." in val:
                    out[key] = float(val)
                    continue
                out[key] = int(val)
                continue
            except ValueError:
                pass

        out[key] = val if val != "" else None
    return out


def _dict_to_row(item: dict, headers: list[str], tab_name: str) -> list:
    """
    הופך dict פנימי לשורה (list) מוכנה לכתיבה לגיליון, מסודרת לפי headers.
    - ממיר שדות dict/list ל-JSON string
    - ממפה שם שדה פנימי לעמודה המתאימה
    """
    # מיפוי: לכל header, מה שם השדה הפנימי המקביל?
    out = []
    for col in headers:
        # אם העמודה היא _json — מחפשים את שם השדה הפנימי המקביל
        if col in JSON_COLS.get(tab_name, set()):
            internal_key = SHEET_TO_INTERNAL.get(col, col)
            val = item.get(internal_key)
            if val is None:
                out.append("")
            else:
                out.append(json.dumps(val, ensure_ascii=False))
        else:
            val = item.get(col, "")
            if val is None:
                val = ""
            out.append(val)
    return out


# ──────────────────────────────────────────────
# קריאות (עם cache קצר להפחתת קריאות API)
# ──────────────────────────────────────────────
@st.cache_data(ttl=15, show_spinner=False)
def _read_tab(tab_name: str) -> list[dict]:
    """
    קורא את כל השורות של טאב ומחזיר רשימת dicts.
    cache של 15 שניות — שומר על ביצועים ומקטין API calls.

    חשוב: משתמשים ב-get_all_values (לא get_all_records) כי get_all_records
    מפרש מספרים וחותך את ה-0 המוביל בטלפונים.
    """
    ws = _ws(tab_name)
    all_rows = ws.get_all_values()
    if len(all_rows) < 2:
        return []
    headers = all_rows[0]
    result = []
    for row in all_rows[1:]:
        # מיישרים את אורך השורה לאורך הכותרות (תאים ריקים בסוף)
        padded = list(row) + [""] * (len(headers) - len(row))
        row_dict = dict(zip(headers, padded))
        result.append(_row_to_dict(row_dict, tab_name))
    return result


def invalidate_cache():
    """מפנה cache של קריאות — קריאה חובה אחרי כל כתיבה."""
    _read_tab.clear()


def get_users() -> list[dict]:
    return _read_tab("users")


def get_bulk_deals() -> list[dict]:
    return _read_tab("bulk_deals")


def get_share_items() -> list[dict]:
    return _read_tab("share_items")


def get_gig_jobs() -> list[dict]:
    return _read_tab("gig_jobs")


def get_activities() -> list[dict]:
    return _read_tab("activities")


# ──────────────────────────────────────────────
# כתיבות
# ──────────────────────────────────────────────
def _append_row(tab_name: str, item: dict):
    ws = _ws(tab_name)
    headers = ws.row_values(1)
    row = _dict_to_row(item, headers, tab_name)
    ws.append_row(row, value_input_option="RAW")
    invalidate_cache()


def _update_by_id(tab_name: str, item: dict, id_field: str = "id"):
    """מוצא שורה עם id תואם ומעדכן אותה. מוסיף אם לא קיים."""
    ws = _ws(tab_name)
    headers = ws.row_values(1)
    col_idx_id = headers.index(id_field) + 1  # gspread משתמש ב-1-based
    id_col_vals = ws.col_values(col_idx_id)  # כולל הכותרת

    try:
        row_idx = id_col_vals.index(str(item[id_field])) + 1  # index מ-0, אבל יש כותרת
    except ValueError:
        _append_row(tab_name, item)
        return

    row = _dict_to_row(item, headers, tab_name)
    # עדכון כל השורה בבת אחת
    end_col_letter = gspread.utils.rowcol_to_a1(row_idx, len(headers))
    start_col_letter = gspread.utils.rowcol_to_a1(row_idx, 1)
    ws.update(
        range_name=f"{start_col_letter}:{end_col_letter}",
        values=[row],
        value_input_option="RAW",
    )
    invalidate_cache()


def _delete_by_id(tab_name: str, id_value: str):
    ws = _ws(tab_name)
    headers = ws.row_values(1)
    col_idx_id = headers.index("id") + 1
    id_col_vals = ws.col_values(col_idx_id)
    try:
        row_idx = id_col_vals.index(str(id_value)) + 1
    except ValueError:
        return
    ws.delete_rows(row_idx)
    invalidate_cache()


# ── API חיצוני נוח למודולים ──
def upsert_user(name: str, phone: str):
    """מעדכן last_seen אם המשתמש קיים, אחרת מוסיף חדש עם first_seen."""
    users = get_users()
    now = datetime.now().isoformat(timespec="seconds")
    existing = next((u for u in users if str(u.get("phone", "")).strip() == phone.strip()), None)
    if existing:
        existing["last_seen"] = now
        # שם יכול להשתנות (המשתמש הזין שם שונה בכניסה הבאה)
        existing["name"] = name
        _update_by_id("users", existing, id_field="phone")
    else:
        _append_row("users", {
            "phone": phone,
            "name": name,
            "first_seen": now,
            "last_seen": now,
        })


def add_bulk_deal(deal: dict):       _append_row("bulk_deals", deal)
def update_bulk_deal(deal: dict):    _update_by_id("bulk_deals", deal)
def delete_bulk_deal(id_: str):      _delete_by_id("bulk_deals", id_)

def add_share_item(item: dict):      _append_row("share_items", item)
def update_share_item(item: dict):   _update_by_id("share_items", item)
def delete_share_item(id_: str):     _delete_by_id("share_items", id_)

def add_gig_job(job: dict):          _append_row("gig_jobs", job)
def update_gig_job(job: dict):       _update_by_id("gig_jobs", job)
def delete_gig_job(id_: str):        _delete_by_id("gig_jobs", id_)

def add_activity(act: dict):         _append_row("activities", act)
def update_activity(act: dict):      _update_by_id("activities", act)
def delete_activity(id_: str):       _delete_by_id("activities", id_)
