"""
setup_sheets.py — סקריפט חד-פעמי
==================================
קורא את ה-credentials מ-.streamlit/secrets.toml, מתחבר לגיליון גוגל,
כותב את שורת הכותרות לכל אחד מ-5 הטאבים, ומעצב אותן (Bold + Freeze).

הרץ פעם אחת בלבד:
    python setup_sheets.py
"""
from pathlib import Path
import sys
import io

# Windows console לא מטפל נכון ב-UTF-8 כברירת מחדל — עוטפים את stdout
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib

import gspread
from google.oauth2.service_account import Credentials


# ── מבנה הטאבים: {שם_טאב: רשימת עמודות} ──
TABS = {
    "users": [
        "phone", "name", "first_seen", "last_seen",
    ],
    "bulk_deals": [
        "id", "product_emoji", "name", "supplier",
        "price_retail", "box_size", "price_per_box",
        "business_address", "business_hours", "business_phone",
        "delivery_cost", "target_date", "created_at", "status",
        "organizer_name", "organizer_phone",
        "carrier_json", "participants_json", "comments_json",
    ],
    "share_items": [
        "id", "type", "item_name", "description",
        "owner_name", "phone", "created_at",
    ],
    "gig_jobs": [
        "id", "title", "description", "wage", "wage_type",
        "status", "poster_name", "phone", "created_at",
    ],
    "activities": [
        "id", "type", "title", "description",
        "event_date", "event_time", "location", "total_seats",
        "organizer_name", "phone",
        "participants_json", "volunteers_json", "created_at",
    ],
}


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def main():
    # קריאת הסודות
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print(f"❌ לא נמצא: {secrets_path}")
        sys.exit(1)

    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)

    spreadsheet_id = secrets.get("spreadsheet_id")
    svc_info = secrets.get("gcp_service_account")
    if not spreadsheet_id or not svc_info:
        print("❌ חסרים spreadsheet_id או gcp_service_account ב-secrets.toml")
        sys.exit(1)

    # אימות וחיבור
    creds = Credentials.from_service_account_info(dict(svc_info), scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        sh = client.open_by_key(spreadsheet_id)
    except gspread.exceptions.APIError as e:
        print(f"❌ שגיאה בפתיחת הגיליון: {e}")
        print("   ודא שהגיליון משותף עם:", svc_info["client_email"])
        sys.exit(1)

    print(f"✅ מחובר לגיליון: '{sh.title}'")
    print(f"   URL: {sh.url}\n")

    # רשימת הטאבים הקיימים בגיליון
    existing_tabs = {ws.title for ws in sh.worksheets()}
    print(f"📋 טאבים קיימים: {sorted(existing_tabs)}\n")

    # טיפול בכל טאב
    for tab_name, headers in TABS.items():
        print(f"— מטפל בטאב '{tab_name}':")
        if tab_name not in existing_tabs:
            print(f"  ⚠️  הטאב לא קיים — יוצר אותו")
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=max(len(headers), 20))
        else:
            ws = sh.worksheet(tab_name)

        # קריאת שורה 1 נוכחית כדי לא לדרוס אם יש כבר כותרות תקינות
        first_row = ws.row_values(1)
        if first_row == headers:
            print(f"  ✅ כותרות כבר קיימות — מדלג")
            continue

        # כתיבת הכותרות
        ws.update(range_name="A1", values=[headers])
        # עיצוב — Bold + Freeze שורה 1
        ws.format("A1:1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.90, "green": 0.95, "blue": 0.96},
        })
        sh.batch_update({
            "requests": [{
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": ws.id,
                        "gridProperties": {"frozenRowCount": 1},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            }]
        })
        print(f"  ✅ נכתבו {len(headers)} עמודות + עיצוב")

    print("\n🎉 הכותרות מוכנות!")

    # ── עיצוב עמודות טלפון כטקסט (שלא יאבד 0 מוביל) ──
    format_phone_columns(sh)

    # ── טעינת נתוני דמו (רק אם הגיליון ריק מנתונים) ──
    seed_demo_data(sh)

    print("\n✨ הכל מוכן! האפליקציה מוכנה להתחבר.")
    print(f"   פתח: {sh.url}")


def format_phone_columns(sh):
    """
    מעצב את עמודות הטלפון והמזהים בכל טאב כ-'טקסט פשוט'.
    בלי זה, Google Sheets מפרש '0501234567' כמספר ומאבד את ה-0 המוביל.
    """
    print("\n📞 מעצב עמודות טלפון וmזהים כטקסט...")

    # מיפוי: {שם_טאב: [שמות_עמודות_שצריך_להיות_טקסט]}
    text_cols = {
        "users":       ["phone"],
        "bulk_deals":  ["organizer_phone", "business_phone"],
        "share_items": ["phone"],
        "gig_jobs":    ["phone"],
        "activities":  ["phone", "event_time"],
    }

    for tab_name, cols in text_cols.items():
        ws = sh.worksheet(tab_name)
        headers = ws.row_values(1)
        requests = []
        for col_name in cols:
            if col_name not in headers:
                continue
            col_idx = headers.index(col_name)  # 0-based
            # עיצוב של כל העמודה (מהשורה 2 ועד אינסוף) — repeatCell על grid range
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": ws.id,
                        "startRowIndex": 1,  # מדלג על הכותרת
                        "startColumnIndex": col_idx,
                        "endColumnIndex": col_idx + 1,
                        # ללא endRowIndex = כל העמודה, כולל שורות שייווצרו בעתיד
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "TEXT"}
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            })
        if requests:
            sh.batch_update({"requests": requests})
        print(f"  ✅ '{tab_name}': {len(cols)} עמודות עוצבו כטקסט")


def seed_demo_data(sh):
    """אם טאבים ריקים (רק כותרות) — מוסיף נתוני דמו ראשוניים."""
    import json
    from datetime import date, datetime, timedelta

    print("\n🌱 בודק אם יש צורך לטעון נתוני דמו...")

    demo = {
        "bulk_deals": [
            {
                "id": "demo1",
                "product_emoji": "🫒",
                "name": "שמן זית כתית מעולה",
                "supplier": "מכולת אורי",
                "price_retail": 45.0,
                "box_size": 6,
                "price_per_box": 180.0,
                "business_address": "רחוב הרצל 14, תל אביב",
                "business_hours": "א'–ו' 08:00–20:00",
                "business_phone": "03-5551234",
                "delivery_cost": 25.0,
                "target_date": (date.today() + timedelta(days=5)).isoformat(),
                "created_at": datetime.now().isoformat(),
                "status": "open",
                "organizer_name": "יוסי כהן",
                "organizer_phone": "0501234567",
                "carrier_json": json.dumps({
                    "name": "יוסי כהן", "phone": "0501234567", "type": "with_discount"
                }, ensure_ascii=False),
                "participants_json": json.dumps([
                    {"id": "p1", "name": "יוסי כהן", "phone": "0501234567", "quantity": 2,
                     "need_expiry": (date.today() + timedelta(days=7)).isoformat()},
                    {"id": "p2", "name": "מיה לוי", "phone": "0527654321", "quantity": 1,
                     "need_expiry": (date.today() + timedelta(days=5)).isoformat()},
                ], ensure_ascii=False),
                "comments_json": json.dumps([
                    {"id": "cmt1", "author": "מיה לוי",
                     "text": "מתי הדדליין לאיסוף כסף? אני בחו\"ל עד סוף השבוע.",
                     "created_at": datetime.now().isoformat()}
                ], ensure_ascii=False),
            }
        ],
        "share_items": [
            {"id": "s1", "type": "offer", "item_name": "מקדחה עם מרצע",
             "description": "מקדחה של בוש, מצב מעולה. זמינה לשבוע.",
             "owner_name": "דן ברק", "phone": "0541111222",
             "created_at": datetime.now().isoformat()},
            {"id": "s2", "type": "seek", "item_name": "מדרגה / סולם קצר",
             "description": "צריך לתלות מדפים, מספיק סולם של 3 שלבים.",
             "owner_name": "רחל שמיר", "phone": "0549876543",
             "created_at": datetime.now().isoformat()},
        ],
        "gig_jobs": [
            {"id": "g1", "title": "עזרה בהובלת ריהוט",
             "description": "צריך 2 אנשים לעזור להעביר ספה וארון לקומה 3. כשעתיים עבודה.",
             "wage": 80.0, "wage_type": "per_hour", "status": "open",
             "poster_name": "אלי מזרחי", "phone": "0523334444",
             "created_at": datetime.now().isoformat()},
            {"id": "g2", "title": "שמירה על כלב – סוף שבוע",
             "description": "נסיעה לחו\"ל מחר. צריך מישהו ישר ואחראי.",
             "wage": 200.0, "wage_type": "fixed", "status": "open",
             "poster_name": "נועה גל", "phone": "0535556666",
             "created_at": datetime.now().isoformat()},
        ],
        "activities": [
            {"id": "a1", "type": "activity", "title": "ערב פיצה קהילתי 🍕",
             "description": "מזמינים פיצות ביחד ורואים סרט. כולם מוזמנים!",
             "event_date": (date.today() + timedelta(days=3)).isoformat(),
             "event_time": "20:00", "location": "חדר מועדון, קומה 1", "total_seats": 12,
             "organizer_name": "תמר כץ", "phone": "0547778888",
             "participants_json": json.dumps([{"name": "ידידיה שלום", "phone": "0501112222"}],
                                            ensure_ascii=False),
             "volunteers_json": "",
             "created_at": datetime.now().isoformat()},
            {"id": "a2", "type": "ride", "title": "טרמפ לתל אביב – שישי בצהריים",
             "description": "נוסע ברכבי לת\"א, יש 3 מקומות פנויים.",
             "event_date": (date.today() + timedelta(days=2)).isoformat(),
             "event_time": "13:30", "location": "חניה מרכזית, שער כניסה", "total_seats": 3,
             "organizer_name": "עידו פרץ", "phone": "0529990000",
             "participants_json": "[]", "volunteers_json": "",
             "created_at": datetime.now().isoformat()},
            {"id": "a3", "type": "help_request", "title": "עזרה בהרכבת ארון איקאה",
             "description": "קיבלתי ארון חדש ואני לא מצליחה להבין איך מרכיבים. מחפשת מישהו/מישהי עם ניסיון וקצת סבלנות ☺️",
             "event_date": (date.today() + timedelta(days=1)).isoformat(),
             "event_time": "17:00", "location": "", "total_seats": 0,
             "organizer_name": "שירה אלון", "phone": "0548887777",
             "participants_json": "[]", "volunteers_json": "[]",
             "created_at": datetime.now().isoformat()},
        ],
    }

    for tab_name, items in demo.items():
        ws = sh.worksheet(tab_name)
        existing_rows = ws.get_all_values()
        # שורה 1 = כותרות, אז אם len > 1 סימן שיש נתונים
        if len(existing_rows) > 1:
            print(f"  — '{tab_name}' כבר מכיל נתונים, מדלג")
            continue

        headers = existing_rows[0]
        rows_to_add = []
        for item in items:
            row = [str(item.get(col, "")) if item.get(col) is not None else "" for col in headers]
            rows_to_add.append(row)

        # RAW — טלפונים ישמרו כמחרוזות, לא כמספרים שאיבדו 0 מוביל
        ws.append_rows(rows_to_add, value_input_option="RAW")
        print(f"  ✅ '{tab_name}': הוספו {len(rows_to_add)} שורות דמו")


if __name__ == "__main__":
    main()
