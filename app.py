"""
Kfar-Link – Community ERP for Student Villages
===============================================
אפליקציית קהילה לניהול כפר סטודנטים.
כתובה ב-Python + Streamlit כחלק מ-MVP לתכנית SPM של Wix.

חמישה מודולים:
  1. דף ראשי          – Feed מאוחד של כל הפעילויות בכפר
  2. קבוצת רכישה       – Bulk Buy
  3. השאלת ציוד        – Share Board
  4. עבודות מזדמנות    – Gig Jobs
  5. פעילויות ועזרה הדדית – Activities, Rides & Help Requests
"""

import streamlit as st
from datetime import datetime, date, timedelta
import uuid
import math
import base64 as _b64
import json as _json

import db  # שכבת הגישה ל-Google Sheets (users, bulk_deals, share_items, gig_jobs, activities)


# ─────────────────────────────────────────────────
#  Session Persistence — שמירה/שחזור ב-URL param
# ─────────────────────────────────────────────────
# Streamlit Cloud יוצר session חדש בכל F5.
# הפתרון: שומרים פרטי משתמש מינימליים ב-query param "s" (base64).
# זה גלוי ב-URL אבל אין בו מידע רגיש (רק שם, טלפון, מייל, uid).

def _save_session(user: dict) -> None:
    """שומר את המשתמש ב-URL query param כדי לשרוד refresh."""
    try:
        enc = _b64.urlsafe_b64encode(_json.dumps(user).encode()).decode()
        st.query_params["s"] = enc
    except Exception:
        pass


def _restore_session() -> None:
    """משחזר session מה-URL query param אם session_state ריק."""
    if st.session_state.get("current_user"):
        return
    try:
        enc = st.query_params.get("s", "")
        if enc:
            data = _json.loads(_b64.urlsafe_b64decode(enc.encode() + b"==").decode())
            if data.get("name") and data.get("phone"):
                st.session_state.current_user = data
    except Exception:
        pass

# ─────────────────────────────────────────────────
#  הגדרות דף
# ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Kfar-Link 🏘️",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────
#  CSS – עיצוב נקי וידידותי למובייל
# ─────────────────────────────────────────────────
st.markdown("""
<style>
    /* ───────────────────────────────────────────────
       Kfar-Link - שמח ותוסס! 🎨
       פלטה: כחול, ירוק, סגול, כתום וכל הצבעים!
       ─────────────────────────────────────────────── */

    /* רקע צבעוני לכל הדף */
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #F0FDFA 50%, #CCFBF1 100%) !important;
        min-height: 100vh !important;
    }

    /* כיוון RTL גלובלי */
    .stMarkdown, .stTextInput, .stSelectbox, label, .stRadio {
        direction: rtl;
        text-align: right;
    }

    /* ── Radio label – עיצוב עדין (הוסר כפתור-ניווט הסגול הדוחני) ── */
    /* הערה: בעבר label של stRadio היה מעוצב ככפתור סגול ענק, מה שגרם
       לתווית "ניווט" בצד להיראות ככפתור שלא עושה כלום. הסרנו את העיצוב הזה. */
    .stRadio > label {
        font-weight: 600 !important;
        color: #3d2b70 !important;
        font-size: 1em !important;
    }

    /* ── Sidebar Navigation – כפתורים גדולים, מודגשים ומזמינים ── */
    /* כל פריט ניווט הוא st.button אמיתי (לא radio) — כך גם הקליקביליות גבוהה
       יותר, וגם אפשר לתת לכל אחד עיצוב מלא (צבע, גרדיאנט, hover, active). */
    [data-testid="stSidebar"] .sidebar-nav-header {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.15em !important;
        font-weight: 800 !important;
        color: #3d2b70 !important;
        margin: 10px 0 8px 0 !important;
        letter-spacing: 0.5px !important;
        padding-right: 4px !important;
    }
    /* ── כפתורי ניווט ב-sidebar — targeting לפי st-key-nav_btn_* ── */
    [data-testid="stSidebar"] [class*="st-key-nav_btn_"] button {
        background: linear-gradient(135deg, #ffffff 0%, #f4f6ff 100%) !important;
        color: #3d2b70 !important;
        border: 2px solid #dde1ff !important;
        border-radius: 18px !important;
        padding: 14px 18px !important;
        margin: 4px 0 !important;
        font-family: 'Heebo', 'Rubik', 'Assistant', 'Segoe UI', -apple-system, sans-serif !important;
        font-size: 1.1em !important;
        font-weight: 800 !important;
        text-align: right !important;
        direction: rtl !important;
        box-shadow: 0 4px 14px rgba(102, 126, 234, 0.14) !important;
        transition: all 0.3s ease !important;
        letter-spacing: 0.4px !important;
        min-height: 58px !important;
        width: 100% !important;
        cursor: pointer !important;
    }
    [data-testid="stSidebar"] [class*="st-key-nav_btn_"] button:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        transform: translateX(-4px) scale(1.02) !important;
        box-shadow: 0 10px 26px rgba(102, 126, 234, 0.45) !important;
        border-color: transparent !important;
    }
    [data-testid="stSidebar"] [class*="st-key-nav_btn_"] button p {
        font-weight: 800 !important;
        font-size: 1.05em !important;
        color: inherit !important;
    }
    /* מצב פעיל (הדף הנוכחי) — color-wrap שמוסיף class נוסף */
    [data-testid="stSidebar"] .nav-active-wrap ~ div [class*="st-key-nav_btn_active"] button,
    [data-testid="stSidebar"] [class*="st-key-nav_btn_"][class*="_active"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: transparent !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.5) !important;
    }

    /* ── העלמת 'Press Enter to submit form' גלובלי ── */
    .stTextInput div[data-testid="InputInstructions"],
    .stNumberInput div[data-testid="InputInstructions"],
    .stDateInput div[data-testid="InputInstructions"] {
        display: none !important;
    }

    /* ── כרטיסים – צבעוניים וחיים! ── */
    .kf-card {
        background: linear-gradient(135deg, #ffffff 0%, #CCFBF1 100%) !important;
        border-radius: 24px !important;
        padding: 20px !important;
        margin-bottom: 12px !important;
        border: none !important;
        border-left: 6px solid #0D9488 !important;
        direction: rtl !important;
        box-shadow: 0 6px 20px rgba(0,82,163,0.2) !important;
        transition: all 0.4s ease !important;
    }
    .kf-card:hover {
        box-shadow: 0 12px 32px rgba(0,82,163,0.3) !important;
        transform: translateY(-6px) !important;
    }
    .kf-card-offer {
        background: linear-gradient(135deg, #CCFBF1, #bbdefb) !important;
        border-left-color: #0D9488 !important;
    }
    .kf-card-seek  {
        background: linear-gradient(135deg, #F0FDFA, #c8e6c9) !important;
        border-left-color: #0D9488 !important;
    }
    .kf-card-job   {
        background: linear-gradient(135deg, #fff5f0, #ffccbc) !important;
        border-left-color: #F97316 !important;
    }
    .kf-card-activity {
        background: linear-gradient(135deg, #e0f7fa, #b3e5fc) !important;
        border-left-color: #00bcd4 !important;
    }

    .kf-badge {
        display: inline-block !important;
        padding: 4px 14px !important;
        border-radius: 20px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        margin-right: 6px !important;
    }
    .badge-open     { background:#e0f7f4 !important; color:#004d40 !important; }
    .badge-taken    { background:#FFEDD5 !important; color:#F97316 !important; }
    .badge-done     { background:#eceff1 !important; color:#37474f !important; }
    .badge-offer    { background:#CCFBF1 !important; color:#0D9488 !important; }
    .badge-seek     { background:#F0FDFA !important; color:#0D9488 !important; }

    /* ── כרטיס תרחיש מחיר – צבעוני __ */
    .scenario-card {
        background: linear-gradient(135deg, #F0FDFA, #c8e6c9) !important;
        border-radius: 24px !important;
        padding: 20px !important;
        text-align: center !important;
        direction: rtl !important;
        box-shadow: 0 6px 18px rgba(0,166,81,0.15) !important;
        transition: all 0.4s ease !important;
        border: none !important;
    }
    .scenario-card:hover {
        transform: translateY(-6px) !important;
        box-shadow: 0 12px 30px rgba(0,166,81,0.25) !important;
    }
    .scenario-card.highlighted {
        background: linear-gradient(135deg, #0D9488, #0F766E) !important;
        color: white !important;
        box-shadow: 0 8px 28px rgba(0,166,81,0.35) !important;
    }

    /* ── Flexbox responsive לכרטיסי מחיר ── */
    .price-cards-row {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        direction: rtl;
        margin: 10px 0 14px 0;
    }
    .price-cards-row > .price-card-col {
        flex: 1 1 180px;
        min-width: 160px;
    }

    /* ── מחיר דינמי ── */
    .price-highlight {
        font-size: 2em;
        font-weight: 700;
        color: #0D9488;
    }
    .price-savings {
        font-size: 0.9em;
        color: #6c757d;
        text-decoration: line-through;
    }

    /* ── כפתור WhatsApp ── */
    .wa-btn {
        background-color: #25D366;
        color: white !important;
        padding: 7px 16px;
        border-radius: 25px;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.85em;
        box-shadow: 0 3px 10px rgba(37,211,102,0.25);
        transition: box-shadow 0.15s ease;
    }
    .wa-btn:hover { box-shadow: 0 5px 18px rgba(37,211,102,0.4); }

    /* ── Progress Bar מותאם – צבעי כחול-ירוק ── */
    .kf-progress-wrap {
        background: linear-gradient(90deg, #CCFBF1, #e0f2f1);
        border-radius: 18px;
        height: 32px;
        overflow: hidden;
        position: relative;
        margin: 10px 0;
        box-shadow: inset 0 2px 6px rgba(0,82,163,0.12);
    }
    .kf-progress-fill {
        height: 100%;
        border-radius: 18px;
        transition: width 0.6s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8em;
        font-weight: 700;
        color: #fff;
        text-shadow: 0 1px 3px rgba(0,0,0,0.25);
    }

    /* ── כרטיס דחיפות (אדום) ── */
    .urgency-card {
        background: #ffffff !important;
        border: 2px solid #dc2626 !important;
        border-radius: 32px !important;
        padding: 24px !important;
        margin-bottom: 14px !important;
        direction: rtl !important;
        box-shadow: 0 4px 18px rgba(220,38,38,0.15) !important;
    }
    .urgency-header {
        background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
        color: white !important;
        border-radius: 28px !important;
        padding: 16px 24px !important;
        margin-bottom: 18px !important;
        direction: rtl !important;
        text-align: center !important;
        font-weight: 700 !important;
        font-size: 1.1em !important;
        box-shadow: 0 4px 16px rgba(220,38,38,0.25) !important;
    }

    /* ── הודעת ניצחון (ירוק) ── */
    .victory-card {
        background: linear-gradient(135deg, #e0f2f1, #c8e6c9) !important;
        border: 2px solid #0D9488 !important;
        border-radius: 32px !important;
        padding: 24px !important;
        direction: rtl !important;
        text-align: center !important;
        margin-bottom: 14px !important;
        box-shadow: 0 4px 20px rgba(0,166,81,0.18) !important;
    }

    /* ── הודעת 'אין משלוח' ── */
    .no-delivery-card {
        background: #ffffff !important;
        border-radius: 32px !important;
        padding: 24px !important;
        text-align: center !important;
        direction: rtl !important;
        border: 2px solid #F97316 !important;
        box-shadow: 0 3px 14px rgba(255,122,61,0.15) !important;
    }

    /* ── כרטיס בקשת עזרה ── */
    .kf-card-help { border-left-color: #7c3aed; }
    .badge-help   { background:#f3e5f5; color:#6a1b9a; }

    /* ═══════════════════════════════════════════════
       דף נחיתה – Welcome Screen (עיצוב חדש)
       ═══════════════════════════════════════════════ */
    .landing-hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important;
        border-radius: 40px !important;
        padding: 52px 40px !important;
        text-align: center !important;
        direction: rtl !important;
        margin: 20px auto !important;
        max-width: 700px !important;
        box-shadow: 0 16px 50px rgba(102, 126, 234, 0.4) !important;
        color: white !important;
    }
    .landing-hero h1 {
        font-size: 2.8em !important;
        color: white !important;
        margin: 0 0 16px 0 !important;
        font-weight: 900 !important;
        letter-spacing: 1px !important;
    }
    .landing-emojis {
        font-size: 3em !important;
        letter-spacing: 12px !important;
        margin: 20px 0 28px 0 !important;
        line-height: 1.2 !important;
        animation: bounce 2s infinite !important;
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    .landing-tagline {
        font-size: 1.25em !important;
        color: rgba(255,255,255,0.99) !important;
        margin-bottom: 12px !important;
        font-weight: 700 !important;
    }
    .landing-sub {
        font-size: 1em !important;
        color: rgba(255,255,255,0.9) !important;
        font-weight: 600 !important;
    }

    /* ═══════════════════════════════════════════════
       פיד ראשי – Home Feed (עיצוב חדש)
       ═══════════════════════════════════════════════ */
    .feed-hero-header {
        background: linear-gradient(135deg, #f093fb, #f5576c) !important;
        color: white !important;
        border-radius: 35px !important;
        padding: 18px 28px !important;
        margin: 10px 0 16px 0 !important;
        direction: rtl !important;
        font-weight: 800 !important;
        font-size: 1.15em !important;
        box-shadow: 0 8px 25px rgba(245, 87, 108, 0.4) !important;
        letter-spacing: 0.5px !important;
    }
    .feed-section-header {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-weight: 900 !important;
        font-size: 1.3em !important;
        margin: 28px 0 14px 0 !important;
        direction: rtl !important;
        border-right: 4px solid #667eea !important;
        padding-right: 12px !important;
        letter-spacing: 1px !important;
    }
    .feed-card {
        background: linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%) !important;
        border-radius: 40px !important;
        padding: 24px 20px !important;
        margin-bottom: 14px !important;
        direction: rtl !important;
        cursor: pointer !important;
        border: none !important;
        border-right: 6px solid #0D9488 !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
        transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }
    .feed-card:hover {
        transform: translateY(-8px) scale(1.02) !important;
        box-shadow: 0 16px 40px rgba(0,0,0,0.25) !important;
    }
    .feed-card-bulk     {
        background: linear-gradient(135deg, #ffeaa7, #fdcb6e) !important;
        border-right-color: #F97316 !important;
        font-weight: 600 !important;
    }
    .feed-card-share    {
        background: linear-gradient(135deg, #55efc4, #38ada9) !important;
        border-right-color: #0D9488 !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .feed-card-gig      {
        background: linear-gradient(135deg, #fd79a8, #e84393) !important;
        border-right-color: #7c3aed !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .feed-card-activity {
        background: linear-gradient(135deg, #74b9ff, #0984e3) !important;
        border-right-color: #00bcd4 !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .feed-card-ride     {
        background: linear-gradient(135deg, #a29bfe, #6c5ce7) !important;
        border-right-color: #0D9488 !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .feed-card-help     {
        background: linear-gradient(135deg, #fab1a0, #e17055) !important;
        border-right-color: #7c3aed !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .feed-card-title {
        font-size: 1.15em !important;
        font-weight: 800 !important;
        color: inherit !important;
        margin: 2px 0 6px 0 !important;
        letter-spacing: 0.5px !important;
    }
    .feed-card-summary {
        color: inherit !important;
        font-size: 0.95em !important;
        line-height: 1.5 !important;
        font-weight: 500 !important;
    }
    .feed-card-meta {
        color: inherit !important;
        font-size: 0.85em !important;
        margin-top: 8px !important;
        opacity: 0.9 !important;
        font-weight: 500 !important;
    }
    .feed-type-chip {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75em;
        font-weight: 700;
        margin-left: 6px;
    }
    .chip-bulk     { background:#fff5f0 !important; color:#0D9488 !important; }
    .chip-share    { background:#F0FDFA !important; color:#0D9488 !important; }
    .chip-gig      { background:#f3e5f5 !important; color:#7c3aed !important; }
    .chip-activity { background:#e0f7fa !important; color:#00bcd4 !important; }
    .chip-ride     { background:#CCFBF1 !important; color:#0D9488 !important; }
    .chip-help     { background:#f3e5f5 !important; color:#7c3aed !important; }

    /* Google Fonts – Heebo (עברית מודרנית, ברורה, ידידותית) */
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800;900&display=swap');

    /* כפתור "לפרטים" מתחת לכרטיס פיד — עיצוב עדין, מחובר לכרטיס.
       הכרטיס עצמו מרונדר כ-HTML טהור עם inline styles, כך שהצבעים
       מובטחים ללא תלות ב-CSS selectors של Streamlit. */
    [class*="st-key-feed_"] button {
        background: rgba(255,255,255,0.55) !important;
        border: 1px solid rgba(0,0,0,0.09) !important;
        border-radius: 0 0 14px 14px !important;
        color: #374151 !important;
        font-size: 0.82em !important;
        font-weight: 700 !important;
        padding: 5px 14px !important;
        margin-top: -2px !important;
        text-align: center !important;
        height: auto !important;
        min-height: 0 !important;
        box-shadow: none !important;
        transition: background 0.2s ease !important;
    }
    [class*="st-key-feed_"] button:hover {
        background: rgba(255,255,255,0.85) !important;
        transform: none !important;
        filter: none !important;
    }

    /* ── שורת Filter Chips ──────────────────────────────────────────
       כפתורים קטנים ועגולים לסינון הפיד לפי סוג.
       הכפתור הפעיל מקבל label עם "✓ " — ה-CSS רק מעצב אותם כ-pills. */
    [class*="st-key-filter_chip_"] button {
        border-radius: 20px !important;
        padding: 3px 8px !important;
        font-size: 0.76em !important;
        font-weight: 700 !important;
        min-height: 0 !important;
        height: 30px !important;
        border: 1.5px solid rgba(0,0,0,0.10) !important;
        background: white !important;
        color: #374151 !important;
        transition: background 0.15s ease !important;
        box-shadow: none !important;
        white-space: nowrap !important;
    }
    [class*="st-key-filter_chip_"] button:hover {
        background: #f1f5f9 !important;
        transform: none !important;
        filter: none !important;
    }

    /* ── גם על קוביות .feed-btn-wrap הישנות (אם נשארו בשימוש) ── */
    .feed-btn-wrap { direction: rtl; margin-bottom: 8px; }

    /* ── העשרת צבעוניות כללית של האתר ── */
    /* רקע עדין יותר + הופעת גרדיאנט עדין ברחבי האתר */
    .stApp {
        background: linear-gradient(135deg, #fff5f8 0%, #eef4ff 35%, #e8fff4 70%, #fff9e8 100%) !important;
    }

    /* Sidebar – רקע מעודן בגוון לבנדר */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f3f0ff 0%, #ebf4ff 100%) !important;
    }

    /* כותרות ראשיות מקבלות גופן עברי */
    h1, h2, h3, h4, h5, h6, p, span, div {
        font-family: 'Heebo', 'Rubik', 'Assistant', 'Segoe UI', -apple-system, sans-serif;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
#  אתחול Session State – טוען מ-Google Sheets
# ─────────────────────────────────────────────────
def init_state():
    """
    טוען את כל מבני הנתונים מ-Google Sheets אל session_state.
    נקרא בכל rerun של Streamlit — הקריאות מוגנות ע"י cache_data(ttl=15)
    ב-db.py, כך שלא נזרק API calls מיותרים.
    חשוב: session_state פה משמש כ-cache מקומי; המקור האמיתי הוא הגיליון.
    """
    st.session_state.bulk_deals  = db.get_bulk_deals()
    st.session_state.share_items = db.get_share_items()
    st.session_state.gig_jobs    = db.get_gig_jobs()
    st.session_state.activities  = db.get_activities()

    if "current_user" not in st.session_state:
        # current_user = None אם לא מחובר, או {"name": str, "phone": str} אם כן.
        # הטלפון משמש כמזהה ייחודי בכל הפעולות.
        st.session_state.current_user = None


# ─────────────────────────────────────────────────
#  פונקציות עזר גנריות
# ─────────────────────────────────────────────────
def gen_id() -> str:
    return str(uuid.uuid4())[:8]


def fmt_phone(phone: str) -> str:
    """מנרמל מספר טלפון ישראלי לפורמט בינלאומי ל-WhatsApp."""
    phone = phone.strip().replace("-", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "972" + phone[1:]
    return phone


def whatsapp_link(phone: str, message: str = "") -> str:
    """מייצר לינק ל-WhatsApp עם הודעה מוכנה מראש."""
    import urllib.parse
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{fmt_phone(phone)}?text={encoded}"


def require_login(action_label: str = "לבצע פעולה זו") -> bool:
    """
    שומר-סף לפעולות כתיבה: בודק אם המשתמש הזדהה.
    משמש לפני כל טופס שדורש זהות (הצטרפות, פרסום, תגובה וכו').
    מחזיר True אם מחובר, False + הודעה אם לא.
    """
    if st.session_state.get("current_user"):
        return True
    st.info(f"🔒 אנא הזדהה ב-Sidebar כדי {action_label}.")
    return False


# ═══════════════════════════════════════════════════════════════════
#  מודול 1 – קבוצת רכישה (Bulk Buy)
# ═══════════════════════════════════════════════════════════════════

def remove_expired_participants(deal: dict) -> dict:
    """
    מסיר משתתפים שפג תאריך תפוגת הצורך שלהם.

    הלוגיקה העסקית:
    ─────────────────
    כל משתתף מצהיר עד מתי הוא *צריך* את המוצר.
    אם התאריך חלף – סימן שהוא כנראה כבר קנה בעצמו או ויתר.
    הסרה אוטומטית מונעת 'פנטום-ביינגס' – משתתפים שמנפחים
    את הקבוצה על הנייר אבל לא יקנו בסוף, מה שמפחית את
    יכולת הקבוצה להגיע לתמחור טוב.
    """
    today = date.today().isoformat()
    before = len(deal["participants"])
    deal["participants"] = [
        p for p in deal["participants"]
        if p["need_expiry"] >= today
    ]
    removed = before - len(deal["participants"])
    return deal, removed


def calculate_bulk_price(deal: dict) -> dict:
    """
    חישוב מחיר דינמי מבוסס 'ארגזים'.

    הלוגיקה העסקית:
    ─────────────────
    הספק מוכר רק בארגזים שלמים (box_size יחידות לארגז).
    ככל שהקבוצה גדלה → צריך יותר ארגזים → אבל המחיר-ליחידה
    מהספק כבר קבוע (price_per_box / box_size).
    הרווח לקבוצה נובע מכך שלפעמים ארגז עולה הרבה פחות
    מקניה קמעונאית – לכן המחיר ליחידה מהספק אמור להיות
    נמוך ממחיר הקמעונאי.

    'יחידות עודפות': כאשר מעגלים ארגזים למעלה, נשארות יחידות
    שאפשר לחלק בחינם/בעלות נמוכה בין המשתתפים.
    """
    participants = deal["participants"]
    # מחיר יעד תמיד מחושב מהספק, גם כשאין משתתפים עדיין –
    # כדי שהמשתמש יראה מיד מה הוא ירוויח אם יצטרף.
    target_price = round(deal["price_per_box"] / deal["box_size"], 2)
    if not participants:
        return {
            "price_per_unit": deal["price_retail"],
            "target_price": target_price,
            "total_units": 0,
            "full_boxes": 0,
            "units_to_next_box": deal["box_size"],
            "units_leftover": 0,
            "total_cost": 0.0,
            "savings_pct": 0.0,
            "box_fill_ratio": 0.0,
            "box_is_full": False,
        }

    total_units = sum(p["quantity"] for p in participants)
    box_size = deal["box_size"]
    price_per_box = deal["price_per_box"]

    # מעגלים למעלה – הספק מוכר ארגזים שלמים בלבד
    full_boxes_needed = math.ceil(total_units / box_size)

    # עלות כוללת מהספק
    total_cost = full_boxes_needed * price_per_box

    # מחיר אפקטיבי ליחידה (לפני סבסוד שליח)
    price_per_unit = total_cost / total_units

    # כמה יחידות קיבלנו 'בונוס' בגלל עיגול ארגז למעלה
    units_leftover = (full_boxes_needed * box_size) - total_units

    # חיסכון ביחס למחיר קמעונאי
    savings_pct = max(0.0, (deal["price_retail"] - price_per_unit) / deal["price_retail"] * 100)

    # מחיר יעד = מחיר ליחידה כשארגז אחד מלא לגמרי.
    # זהו המחיר ה'מובטח' של המבצע שמוצג בבולט למשתמש.
    target_price = round(price_per_box / box_size, 2)

    # חישוב מילוי ארגז נוכחי: כמה יחידות הוזמנו לעומת היעד לארגז הבא
    # אם total_units מתחלק ב-box_size בדיוק – ארגז מלא!
    units_to_next_box = full_boxes_needed * box_size   # היעד לארגז הנוכחי
    box_fill_ratio = total_units / units_to_next_box    # 0.0 – 1.0 (1.0 = ארגז מלא)
    box_is_full = (total_units % box_size == 0)         # האם הארגז סגור?

    # ── פירוט מילוי כל ארגז בנפרד ──
    # כל ארגז מקבל את מנת היחידות שלו:
    # ארגזים מלאים = box_size, ארגז אחרון = שארית
    boxes_detail = []
    units_remaining = total_units
    for b in range(full_boxes_needed):
        units_in_box = min(units_remaining, box_size)
        units_remaining -= units_in_box
        boxes_detail.append({
            "box_num": b + 1,
            "units": units_in_box,
            "capacity": box_size,
            "fill_pct": round(units_in_box / box_size * 100),
            "is_full": units_in_box == box_size,
        })

    return {
        "price_per_unit": round(price_per_unit, 2),
        "target_price": target_price,
        "total_units": total_units,
        "full_boxes": full_boxes_needed,
        "units_to_next_box": units_to_next_box,
        "units_leftover": units_leftover,
        "total_cost": round(total_cost, 2),
        "savings_pct": round(savings_pct, 1),
        "box_fill_ratio": round(box_fill_ratio, 3),
        "box_is_full": box_is_full,
        "boxes_detail": boxes_detail,
    }


def get_hero_info(deal: dict, price_per_unit: float) -> dict | None:
    """
    מחשב את פרטי ה'גיבור שליחות' והנחתו.

    הלוגיקה העסקית:
    ─────────────────
    מתנדב לאסוף/לחלק את ההזמנה מקבל הנחה של 5%
    על סך הרכישה שלו, מוגבלת ל-20₪ מקסימום.
    זוהי הנחה 'חברתית': לא צריך לשלם לשליח בנפרד – במקום זאת,
    הגיבור מקבל פרס ישיר על הרכישה שלו, מה שמוריד חיכוך
    ומתמרץ התנדבות אמיתית.
    """
    HERO_DISCOUNT_RATE = 0.05  # 5% הנחה לגיבור השליחות
    HERO_DISCOUNT_CAP  = 20.0  # תקרה: 20₪ מקסימום

    heroes = [p for p in deal["participants"] if p.get("is_delivery_hero")]
    if not heroes:
        return None

    hero = heroes[0]
    original_cost = hero["quantity"] * price_per_unit
    discount_raw  = original_cost * HERO_DISCOUNT_RATE
    discount_amount = min(discount_raw, HERO_DISCOUNT_CAP)  # תקרת 20₪
    final_cost = original_cost - discount_amount

    return {
        "name": hero["name"],
        "phone": hero["phone"],
        "original_cost": round(original_cost, 2),
        "discount": round(discount_amount, 2),
        "final_cost": round(final_cost, 2),
    }


def select_winning_volunteer(deal: dict) -> dict | None:
    """
    מחזיר את המוביל הנוכחי של העסקה.

    הלוגיקה:
    ─────────
    המוביל מאוחסן ב-deal['carrier'] – שדה ייעודי שנפרד לחלוטין
    ממשתתפים. זה מאפשר פעולת הובלה עצמאית שאינה כרוכה בקנייה.

    היררכיית עדיפויות (נאכפת בעת רישום):
    1. no_discount – תמיד מחליף with_discount אם הוא רוצה.
    2. with_discount – נכנס רק אם אין מוביל כלל.
    """
    carrier = deal.get("carrier")
    if not carrier:
        return None
    type_label = (
        "מתנדב בחינם – הכי טוב לקבוצה ✨"
        if carrier.get("type") == "no_discount"
        else "גיבור משלוחים (5% הנחה, עד 20₪)"
    )
    return {**carrier, "volunteer_type": carrier.get("type"), "selection_reason": type_label}


def calculate_scenario_prices(deal: dict, pricing: dict) -> dict:
    """
    מחשבת 3 תרחישי מחיר לכל עסקה – כל התרחישים מבוססים על ארגז מלא.

    ════════════════════════════════════════════════════════
    תרחיש C – מתנדב בחינם (מחיר בסיס):
    ════════════════════════════════════════════════════════
      base_ppu = price_per_box / box_size
      הכי זול ⭐ – מתנדב מגיע בחינם, כולם משלמים מחיר בסיס.

    ════════════════════════════════════════════════════════
    תרחיש A – משלוח חיצוני:
    ════════════════════════════════════════════════════════
      price_A = (price_per_box + delivery_cost) / box_size
      עלות ארגז + משלוח, מחולקת שווה בין כל היחידות.

    ════════════════════════════════════════════════════════
    תרחיש B – גיבור משלוחים (מודל דמי נסיעה קבועים):
    ════════════════════════════════════════════════════════
    הפרדה שקופה בין עלות המוצר לעלות הנסיעה:

      ── עלות מוצר (לכולם, כולל הגיבור) ──
        כל אחד משלם base_ppu × יחידות שלו.
        הגיבור לא מקבל הנחה על המוצר – שוויוני לגמרי.

      ── דמי נסיעה (רק האחרים, לא הגיבור) ──
        TRIP_FEE_MAX = 20₪  (הסכום שהגיבור יכול לקבל על הנסיעה)

        כל אחד מהאחרים תורם חלק יחסי מ-20₪ לפי יחידות:
          trip_per_other_unit = min(TRIP_FEE_MAX, max_trip) / others_units

        תקרת קמעונאי (הגנת הצרכן):
          max_trip = (price_retail − base_ppu) × others_units
          → האחרים לעולם לא ישלמו מעל מחיר קמעונאי.

        actual_trip = min(TRIP_FEE_MAX, max_trip)
          → אם יש מעט אחרים, הגיבור יקבל פחות מ-20₪ (הם מוגנים).
          → אם יש מספיק אחרים, הגיבור יקבל 20₪ מלאים.

      ── תוצאה ──
        מחיר לאחרים = base_ppu + actual_trip / others_units
        מחיר ברוטו לגיבור = base_ppu (מוצר בלבד)
        תשלום נסיעה לגיבור = actual_trip
        מחיר נטו לגיבור/יח' = base_ppu − actual_trip / hero_units

      ── אופטימיזציה אוטומטית ──
        אם others_ppu >= price_A + 0.01 → auto-switch למשלוח חיצוני.
    """
    TRIP_FEE_MAX = 20.0   # תשלום נסיעה מקסימלי לגיבור – קבוע ושקוף

    box_size      = deal["box_size"]
    price_per_box = deal["price_per_box"]
    delivery_cost = deal.get("delivery_cost", 0.0)
    price_retail  = deal.get("price_retail", float("inf"))  # תקרת קמעונאי
    total_units   = pricing["total_units"]

    # ════════════════════════════════════════════════════════
    #  STEP 0: מחיר בסיס ומחיר משלוח חיצוני
    # ════════════════════════════════════════════════════════
    # לא מעגלים כאן – מונעים drift מצטבר בשלבי חישוב
    base_ppu = price_per_box / box_size
    price_A  = round((price_per_box + delivery_cost) / box_size, 2)

    # ════════════════════════════════════════════════════════
    #  STEP 1: כמות יחידות הגיבור
    # ════════════════════════════════════════════════════════
    # מחפשים את הגיבור לפי טלפון. אם לא נמצא – 1 יחידה תיאורטית.
    carrier = deal.get("carrier")
    if carrier and carrier.get("type") == "with_discount":
        cp = next(
            (p for p in deal["participants"] if p.get("phone") == carrier.get("phone")),
            None
        )
        hero_units = cp["quantity"] if cp else 1
    else:
        hero_units = 1  # תיאורטי – B מחושב גם ללא גיבור פעיל

    others_units_B = max(total_units - hero_units, 0)

    # ════════════════════════════════════════════════════════
    #  STEP 2: חישוב דמי הנסיעה שנגבים מהאחרים
    #
    #  כמה האחרים יכולים לתרום (max) מבלי לחצות מחיר קמעונאי:
    #    max_trip_from_others = max(price_retail - base_ppu, 0) × others_units
    #
    #  דמי הנסיעה בפועל (actual):
    #    actual_trip = min(TRIP_FEE_MAX, max_trip_from_others)
    #    → מוגבל גם מלמעלה (20₪) וגם מלמטה (מה שהאחרים יכולים)
    # ════════════════════════════════════════════════════════
    if others_units_B > 0:
        # תקרת קמעונאי: כמה האחרים יכולים לשלם מעבר לבסיס?
        max_trip_from_others = max(price_retail - base_ppu, 0.0) * others_units_B
        # דמי הנסיעה בפועל: מינימום בין 20₪ לבין מה שהאחרים יכולים
        actual_trip = min(TRIP_FEE_MAX, max_trip_from_others)
        # מחיר ליחידה לאחרים = בסיס + חלק מדמי הנסיעה
        others_price_B = round(base_ppu + actual_trip / others_units_B, 2)
    else:
        # הגיבור הוא המשתתף היחיד – אין מי שישלם נסיעה
        actual_trip    = 0.0
        others_price_B = round(base_ppu, 2)

    # ════════════════════════════════════════════════════════
    #  STEP 3: מחירים לגיבור
    #
    #  גיבור משלם base_ppu על המוצר (שוויוני לכולם).
    #  בנוסף הוא מקבל תשלום actual_trip עבור הנסיעה.
    #  מחיר נטו ליחידה = base_ppu − actual_trip / hero_units
    # ════════════════════════════════════════════════════════
    hero_price_B    = round(base_ppu, 2)                                   # ברוטו
    hero_net_ppu_B  = round(base_ppu - actual_trip / hero_units, 2)        # נטו

    # ════════════════════════════════════════════════════════
    #  STEP 4: תרחיש C – מתנדב בחינם
    # ════════════════════════════════════════════════════════
    price_C = base_ppu

    # ════════════════════════════════════════════════════════
    #  STEP 5: אופטימיזציה אוטומטית
    #  אם others_ppu >= price_A + 0.01 → משלוח חיצוני עדיף → auto-switch
    # ════════════════════════════════════════════════════════
    hero_more_expensive = (others_price_B >= price_A + 0.01) and (delivery_cost > 0)

    return {
        "A": {"price_per_unit": price_A, "label": "🚚 משלוח חיצוני"},
        "B": {
            "hero_price":          hero_price_B,       # מחיר ברוטו לגיבור (מוצר בלבד)
            "hero_net_ppu":        hero_net_ppu_B,     # מחיר נטו לגיבור (אחרי תשלום נסיעה)
            "others_price":        others_price_B,     # מחיר לשאר (מוצר + חלק נסיעה)
            "trip_payment":        round(actual_trip, 2),  # כמה הגיבור מקבל על הנסיעה
            "hero_discount_ils":   round(actual_trip, 2),  # לתאימות אחורה
            "label":               "🦸 גיבור משלוחים",
            "hero_more_expensive": hero_more_expensive,
        },
        "C": {"price_per_unit": round(price_C, 2), "label": "💚 מתנדב בחינם"},
    }


def get_deal_status(deal: dict, pricing: dict) -> dict:
    """
    קובעת את מצב העסקה לפי שני קריטריונים בלבד:
      1. האם הארגז הגיע ל-100%?
      2. האם הדדליין עבר?

    רק שילוב של ארגז מלא + דדליין לא עבר = עסקה תקפה להזמנה.
    אם הדדליין עבר לפני שהארגז מלא → ביטול אוטומטי.
    זה מונע עסקאות זומבי שתלויות לנצח.
    """
    today       = date.today().isoformat()
    target_date = deal.get("target_date", "")
    total_units = pricing["total_units"]
    box_is_full = pricing.get("box_is_full", False) and total_units > 0

    # האם הדדליין עבר? (מחשבים רק אם יש תאריך יעד)
    deadline_passed = bool(target_date) and target_date < today

    if box_is_full:
        # ארגז מלא לפני הדדליין – עסקה מוצלחת
        return {"code": "closed",
                "icon": "🟢", "label": "ארגז מלא – להזמנה! 🎉", "color": "success"}
    elif deadline_passed:
        # הדדליין עבר לפני שהארגז התמלא – ביטול
        return {"code": "cancelled",
                "icon": "🔴", "label": "הדדליין עבר – העסקה בוטלה", "color": "error"}
    elif total_units > 0:
        # יש משתתפים, ממתינים לעוד
        return {"code": "conditional",
                "icon": "🟡", "label": "מותנית – ממתינים לארגז מלא", "color": "warning"}
    else:
        return {"code": "empty",
                "icon": "⚪", "label": "טרם הצטרפו משתתפים", "color": "info"}


def render_scenario_card_to_streamlit(icon, title, main_price, accent_color, star=False):
    """
    מרנדר כרטיס תרחיש מחיר קומפקטי ישירות ל-Streamlit.
    כל כרטיס מרונדר ב-st.markdown() נפרד – פותר בעיות HTML escaping.
    """
    border = "2px solid #00897b" if star else "1px solid #e0e0e0"
    star_line = ""
    if star:
        star_line = (
            '<span style="background:#d4edda; color:#155724; border-radius:8px; '
            'padding:1px 8px; font-size:0.7em; font-weight:700; margin-right:6px;">'
            '⭐ הכי זול</span>'
        )
    html = (
        f'<div style="background:#fff; border-radius:16px; padding:12px 10px; '
        f'text-align:center; direction:rtl; border:{border};">'
        f'<div style="font-size:1.2em; margin-bottom:2px;">{icon}</div>'
        f'<div style="font-weight:600; color:#555; font-size:0.75em; line-height:1.2;">{title}</div>'
        f'<div style="font-size:1.5em; font-weight:800; color:{accent_color}; margin:4px 0;">{main_price}₪</div>'
        f'{star_line}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_hero_card_to_streamlit(hero_price, others_price):
    """
    מרנדר כרטיס גיבור עם שני מחירים ישירות ל-Streamlit.
    """
    html = (
        f'<div style="background:#fff; border-radius:25px; padding:20px 16px; '
        f'text-align:center; direction:rtl; border:1px solid #e0e0e0; '
        f'box-shadow:0 4px 20px rgba(0,0,0,0.06);">'
        f'<div style="font-size:1.5em; margin-bottom:4px;">🦸</div>'
        f'<div style="font-weight:700; color:#333; margin:4px 0; font-size:0.9em; line-height:1.3;">'
        f'מחיר ליחידה<br>גיבור משלוחים</div>'
        f'<div style="font-size:1.6em; font-weight:800; color:#17a2b8; margin:6px 0;">'
        f'{hero_price}₪ לגיבור</div>'
        f'<div style="font-size:1.1em; font-weight:700; color:#555; margin:2px 0;">'
        f'{others_price}₪ לשאר</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_no_delivery_card_to_streamlit():
    """מרנדר כרטיס 'איסוף מהעסק בלבד' – קומפקטי."""
    html = (
        '<div style="background:#fff; border-radius:16px; padding:12px 10px; '
        'text-align:center; direction:rtl; border:2px solid #f4511e;">'
        '<div style="font-size:1.2em; margin-bottom:2px;">🏪</div>'
        '<div style="font-weight:600; color:#721c24; font-size:0.75em; line-height:1.2;">'
        'איסוף מהעסק בלבד</div>'
        '<div style="font-size:0.7em; color:#856404; margin-top:4px;">'
        'נדרש מתנדב שיאסוף</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def show_bulk_buy():
    """מסך קבוצת הרכישה."""
    st.title("🛒 קבוצת רכישה")
    st.caption("קנו יחד, שלמו פחות. כל שכן שמצטרף מוריד את המחיר! 🏄‍♂️")

    # ══════════════════════════════════════════════════════════════
    #  אזור דחיפות ראשי – עסקאות שפוגות ב-48 השעות הקרובות
    #
    #  עיקרון UX: 'Urgency drives conversion'. הצגת עסקאות
    #  שקרובות לפקיעה בראש הדף גורמת למשתמש לפעול מיד
    #  במקום לדפדף ולשכוח.
    # ══════════════════════════════════════════════════════════════
    today = date.today()
    deadline_48h = today + timedelta(hours=48)  # 48 שעות קדימה
    urgent_deals = []
    for d in st.session_state.bulk_deals:
        td_str = d.get("target_date", "")
        if not td_str:
            continue
        try:
            td_date = date.fromisoformat(td_str)
        except ValueError:
            continue
        # עסקה דחופה = דדליין בתוך 48 שעות, לא עברה, והארגז לא מלא
        if today <= td_date <= deadline_48h:
            p = calculate_bulk_price(d)
            if not (p.get("box_is_full", False) and p["total_units"] > 0):
                days_left = (td_date - today).days
                hours_left = days_left * 24  # הערכה גסה – מספיקה ל-UI
                urgent_deals.append((d, p, days_left, hours_left))

    if urgent_deals:
        st.markdown(
            '<div class="urgency-header">'
            '⏰ עסקאות עומדות להתבטל בקרוב! הצטרפו עכשיו כדי שלא נפספס את ההנחה'
            '</div>',
            unsafe_allow_html=True,
        )
        for ud, up, u_days, u_hours in urgent_deals:
            fill = up.get("box_fill_ratio", 0)
            fill_pct = round(fill * 100)
            units_left = up.get("units_to_next_box", ud["box_size"]) - up["total_units"]
            target_p = up.get("target_price", ud["price_retail"])
            if u_days > 0:
                time_txt = f"⏰ נותר{'ו' if u_days != 1 else ''} <strong>{u_days} {'ימים' if u_days != 1 else 'יום'}</strong> בלבד!"
            else:
                time_txt = "⏰ <strong>היום הוא היום האחרון!</strong>"
            st.markdown(
                f"""
                <div class="urgency-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                        <div>
                            <strong style="font-size:1.15em;color:#c0392b;">⚠️ {ud['name']}</strong>
                            <span style="color:#856404;font-size:0.85em;margin-right:8px;">ספק: {ud['supplier']}</span>
                        </div>
                        <div style="text-align:left;">
                            <span style="font-size:1.5em;font-weight:800;color:#1a7f4b;">{target_p}₪</span>
                            <span style="font-size:0.8em;color:#999;text-decoration:line-through;margin-right:4px;">{ud['price_retail']}₪</span>
                        </div>
                    </div>
                    <div style="margin-top:8px;font-size:0.92em;color:#333;">
                        📦 מילוי ארגז: <strong>{fill_pct}%</strong> — חסרות <strong>{units_left}</strong> יחידות &nbsp;|&nbsp;
                        {time_txt}
                    </div>
                    <div style="margin-top:6px;font-size:0.85em;color:#c0392b;font-weight:600;">
                        🔥 הצטרפו עכשיו לפני שהעסקה מתבטלת!
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.divider()

    tab_browse, tab_new = st.tabs(["📋 עסקאות פעילות", "➕ הצע עסקה חדשה"])

    # ── קפיצה ישירה מהפיד: פותחים אוטומטית את 'פרטים והצטרפות' לעסקה שנבחרה ──
    # (pop חד-פעמי — אחרי שהפרטים נפתחו, סגירה ידנית לא תיפתח מחדש)
    bulk_focus = st.session_state.pop("_bulk_focus", None)
    if bulk_focus:
        st.session_state[f"show_detail_{bulk_focus}"] = True

    # ── טאב: עיון בעסקאות קיימות ──────────────────────────────
    with tab_browse:
        if not st.session_state.bulk_deals:
            st.info("אין עסקאות פעילות כרגע. היה הראשון להציע!")
        else:
            for i, deal in enumerate(st.session_state.bulk_deals):
                # ── הסרה אוטומטית של משתתפים שפגה תפוגתם ──
                deal, removed = remove_expired_participants(deal)
                st.session_state.bulk_deals[i] = deal
                if removed > 0:
                    st.warning(f"⏰ {removed} משתתפ/ים הוסרו מהעסקה '{deal['name']}' כי תאריך הצורך שלהם עבר.")
                    db.update_bulk_deal(deal)

                pricing     = calculate_bulk_price(deal)
                scenarios   = calculate_scenario_prices(deal, pricing)
                winner      = select_winning_volunteer(deal)
                deal_status = get_deal_status(deal, pricing)

                box_is_full = pricing.get("box_is_full", False) and pricing["total_units"] > 0
                target_date = deal.get("target_date", "—")
                target_p    = pricing.get("target_price", deal["price_retail"])

                # ══════════════════════════════════════════════════
                #  כרטיס עסקה פתוח (ללא Expander) – תצוגת תקציר
                # ══════════════════════════════════════════════════
                sc = deal_status["code"]
                retail_p    = deal["price_retail"]
                savings_pct = round((retail_p - target_p) / retail_p * 100, 1) if retail_p > 0 else 0
                total_u    = pricing["total_units"]
                box_size_d = deal["box_size"]
                boxes_detail = pricing.get("boxes_detail", [])

                # אימוג'י מוצר
                product_emoji = deal.get("product_emoji", "📦")

                # סטטוס משלוח – אייקון דינמי
                carrier_check = deal.get("carrier")
                if carrier_check:
                    delivery_icon = "🛺"
                    delivery_tip  = "יש מוביל!"
                else:
                    delivery_icon = "❓"
                    delivery_tip  = "דרוש מוביל"

                # חישוב דדליין ויזואלי
                deadline_html = ""
                if target_date and target_date != "—":
                    try:
                        td_obj    = date.fromisoformat(target_date)
                        days_left = (td_obj - date.today()).days
                        if days_left > 3:
                            deadline_html = f'<span style="color:#0c5460;font-size:0.82em;">⏰ נותרו {days_left} ימים</span>'
                        elif days_left > 0:
                            deadline_html = f'<span style="color:#856404;font-weight:700;font-size:0.82em;">⏰ נותרו {days_left} ימים בלבד!</span>'
                        elif days_left == 0:
                            deadline_html = '<span style="color:#721c24;font-weight:700;font-size:0.82em;">⏰ נסגר היום!</span>'
                        else:
                            deadline_html = f'<span style="color:#721c24;font-weight:700;font-size:0.82em;">⏰ עבר לפני {abs(days_left)} ימים</span>'
                    except ValueError:
                        deadline_html = ""

                # סטטוס באדג' צבעוני
                if sc == "closed":
                    status_bg = "#d4edda"; status_color = "#155724"; status_txt = "🎉 ארגז מלא!"
                elif sc == "cancelled":
                    status_bg = "#f8d7da"; status_color = "#721c24"; status_txt = "🔴 בוטלה"
                elif sc == "warning":
                    status_bg = "#fff3cd"; status_color = "#856404"; status_txt = "⚠️ דדליין קרוב"
                else:
                    status_bg = "#d1ecf1"; status_color = "#0c5460"; status_txt = "🟢 פעילה"

                # ── בניית HTML לכל ארגז בנפרד ──
                boxes_html = ""
                if boxes_detail:
                    for bx in boxes_detail:
                        bfill = bx["fill_pct"]
                        if bfill < 40:
                            bg = "linear-gradient(90deg, #80deea, #4dd0e1)"
                        elif bfill < 75:
                            bg = "linear-gradient(90deg, #4dd0e1, #00acc1)"
                        else:
                            bg = "linear-gradient(90deg, #00acc1, #00796b)"
                        btxt = "מלא!" if bx["is_full"] else f'{bx["units"]}/{bx["capacity"]}'
                        box_label = f'ארגז {bx["box_num"]}'
                        box_border = "2px solid #00796b" if bx["is_full"] else "1px solid #e0e0e0"
                        check_icon = "✅" if bx["is_full"] else "📦"
                        boxes_html += (
                            f'<div style="margin-bottom:6px;">'
                            f'<div style="font-size:0.78em; color:#555; margin-bottom:2px;">'
                            f'{check_icon} {box_label}: {bx["units"]}/{bx["capacity"]} יחידות</div>'
                            f'<div style="background:#e0e0e0; border-radius:8px; height:18px; '
                            f'overflow:hidden; border:{box_border};">'
                            f'<div style="width:{max(bfill, 6)}%; background:{bg}; height:100%; '
                            f'border-radius:8px; display:flex; align-items:center; justify-content:center; '
                            f'color:#fff; font-size:0.7em; font-weight:700;">{btxt}</div>'
                            f'</div></div>'
                        )
                else:
                    # אין משתתפים עדיין – ארגז ריק אחד
                    boxes_html = (
                        f'<div style="margin-bottom:6px;">'
                        f'<div style="font-size:0.78em; color:#555; margin-bottom:2px;">'
                        f'📦 ארגז 1: 0/{box_size_d} יחידות</div>'
                        f'<div style="background:#e0e0e0; border-radius:8px; height:18px; overflow:hidden;">'
                        f'<div style="width:6%; background:linear-gradient(90deg, #80deea, #4dd0e1); '
                        f'height:100%; border-radius:8px;"></div></div></div>'
                    )

                # ── כרטיס HTML ראשי ──
                st.markdown(
                    f'<div style="background:#fff; border-radius:30px; padding:28px 24px 20px 24px; '
                    f'box-shadow:0 8px 32px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04); '
                    f'border:1px solid #e8e8e8; direction:rtl; margin-bottom:8px; position:relative;">'

                    # ── בועית הנחה בפינה ──
                    f'<div style="position:absolute; top:16px; left:18px; '
                    f'background:linear-gradient(135deg, #ff8a65, #f4511e); color:#fff; '
                    f'border-radius:14px; padding:4px 12px; font-size:0.78em; font-weight:700; '
                    f'box-shadow:0 2px 8px rgba(244,81,30,0.3);">'
                    f'חוסכים {savings_pct}%!</div>'

                    # ── אימוג'י מוצר בעיגול צבעוני ──
                    f'<div style="display:flex; align-items:center; gap:14px; margin-bottom:10px;">'
                    f'<div style="width:56px; height:56px; border-radius:50%; '
                    f'background:linear-gradient(135deg, #e0f2f1, #b2dfdb); '
                    f'display:flex; align-items:center; justify-content:center; font-size:1.8em; '
                    f'box-shadow:0 3px 12px rgba(0,150,136,0.15);">{product_emoji}</div>'
                    f'<div>'
                    f'<div style="font-size:1.2em; font-weight:800; color:#222;">{deal["name"]}</div>'
                    f'<div style="font-size:0.78em; color:#888;">ספק: {deal["supplier"]} · הופק ע"י: {deal.get("organizer_name","—")}</div>'
                    f'</div></div>'

                    # ── שורת מחיר + סטטוס + משלוח ──
                    f'<div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:8px;">'
                    f'<span style="font-size:1.8em; font-weight:800; color:#1a7f4b;">{target_p}₪</span>'
                    f'<span style="font-size:0.9em; color:#aaa; text-decoration:line-through;">{retail_p}₪</span>'
                    f'<span style="background:{status_bg}; color:{status_color}; border-radius:10px; '
                    f'padding:2px 8px; font-size:0.75em; font-weight:600;">{status_txt}</span>'
                    f'<span style="font-size:0.78em; color:#555;">{delivery_icon} {delivery_tip}</span>'
                    f'</div>'

                    # ── ארגזים – כל ארגז עם פרוגרס בר משלו ──
                    f'<div style="margin-bottom:6px;">'
                    f'<div style="font-size:0.8em; color:#555; margin-bottom:4px; font-weight:600;">'
                    f'📦 סה"כ: {total_u} יחידות ({len(boxes_detail)} ארגזים)</div>'
                    f'{boxes_html}'
                    f'</div>'

                    # ── דדליין + FOMO ──
                    f'<div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">'
                    f'{deadline_html}'
                    f'<span style="font-size:0.78em; color:#00796b;">'
                    f'👥 {len(deal["participants"])} שכנים בעסקה</span>'
                    f'</div>'

                    f'</div>',
                    unsafe_allow_html=True,
                )

                # ── כפתור 'לפרטים והצטרפות' – מפעיל session_state toggle ──
                detail_key = f"show_detail_{deal['id']}"
                if st.button(
                    "🔎 לפרטים והצטרפות" if not st.session_state.get(detail_key) else "🔼 הסתר פרטים",
                    key=f"detail_btn_{deal['id']}",
                    use_container_width=True,
                    type="primary" if not st.session_state.get(detail_key) else "secondary",
                ):
                    st.session_state[detail_key] = not st.session_state.get(detail_key, False)
                    st.rerun()

                # ══════════════════════════════════════════════════
                #  אזור מפורט – מוצג רק בלחיצה על הכפתור
                # ══════════════════════════════════════════════════
                if st.session_state.get(detail_key):

                    # ══════════════════════════════════════════════════
                    #  אזור 1: סטטוס קומפקטי + הוראות למארגן
                    # ══════════════════════════════════════════════════
                    if sc == "closed":
                        cu_victory = st.session_state.get("current_user")
                        is_organizer = (
                            cu_victory
                            and cu_victory["phone"].strip() == deal.get("organizer_phone", "").strip()
                        )
                        if is_organizer:
                            st.success(
                                f"👑 **{deal.get('organizer_name','מארגן')}**, הגיע הזמן לפעול!  \n"
                                f"1️⃣ אשר הזמנה מול הספק ({deal.get('supplier','')})  \n"
                                f"2️⃣ שלח בקשת תשלום Bit/Paybox לכל המשתתפים  \n"
                                f"3️⃣ תאם איסוף/משלוח"
                            )
                    elif sc == "cancelled":
                        st.error(f"{deal_status['icon']} {deal_status['label']}")
                    elif sc == "warning":
                        st.warning(f"{deal_status['icon']} {deal_status['label']}")
                    else:
                        st.info(f"{deal_status['icon']} {deal_status['label']}")

                    # ── הארכת דדליין (מארגן בלבד) ──
                    extend_key = f"extend_date_{deal['id']}"
                    if deal_status["code"] in ("conditional", "empty", "cancelled"):
                        if st.button(
                            "📅 ערוך / הארך דדליין (מארגן בלבד)",
                            key=f"extend_btn_{deal['id']}", type="secondary"
                        ):
                            st.session_state[extend_key] = True

                    if st.session_state.get(extend_key):
                        cu_extend = st.session_state.get("current_user")
                        org_phone = deal.get("organizer_phone", "")
                        if not cu_extend:
                            st.warning("🔒 יש להזדהות ב-Sidebar כדי לערוך דדליין.")
                        elif cu_extend["phone"].strip() != org_phone.strip():
                            st.error(f"🚫 רק המארגן ({deal.get('organizer_name','—')}) יכול לשנות את הדדליין.")
                        else:
                            with st.form(key=f"extend_form_{deal['id']}"):
                                e_new_date = st.date_input(
                                    "תאריך יעד חדש *",
                                    min_value=date.today() + timedelta(days=1),
                                    value=date.today() + timedelta(days=7),
                                    key=f"ed_{deal['id']}",
                                )
                                ea, eb = st.columns(2)
                                e_confirm = ea.form_submit_button("✅ עדכן דדליין", type="primary", use_container_width=True)
                                e_cancel  = eb.form_submit_button("❌ ביטול", use_container_width=True)
                                if e_confirm:
                                    st.session_state.bulk_deals[i]["target_date"] = e_new_date.isoformat()
                                    if deal_status["code"] == "cancelled":
                                        st.session_state.bulk_deals[i]["status"] = "open"
                                    db.update_bulk_deal(st.session_state.bulk_deals[i])
                                    st.session_state.pop(extend_key, None)
                                    st.rerun()
                                if e_cancel:
                                    st.session_state.pop(extend_key, None)
                                    st.rerun()

                    st.divider()

                    # ══════════════════════════════════════════════════
                    #  אזור 2: פרטי העסק
                    # ══════════════════════════════════════════════════
                    biz_addr      = deal.get("business_address", "")
                    biz_hours     = deal.get("business_hours", "")
                    biz_phone     = deal.get("business_phone", "")
                    delivery_cost = deal.get("delivery_cost", 0.0)
                    is_no_delivery = deal.get("no_delivery", False)

                    if biz_addr or biz_hours or biz_phone:
                        expander_label = (
                            "🛺 פרטי העסק – איסוף עצמי בלבד" if is_no_delivery
                            else "🛺 פרטי העסק – למתנדב שמגיע לאסוף"
                        )
                        with st.expander(expander_label, expanded=is_no_delivery):
                            if is_no_delivery:
                                st.warning("🚫 **העסק לא מציע משלוח.** נדרש מתנדב שיאסוף את ההזמנה.")
                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if biz_addr:
                                    st.markdown(f"📍 **כתובת:** {biz_addr}")
                                if biz_hours:
                                    st.markdown(f"🕐 **שעות פתיחה:** {biz_hours}")
                                if not is_no_delivery and delivery_cost > 0:
                                    st.markdown(f"🚚 **עלות משלוח חיצוני:** {delivery_cost}₪")
                            with bc2:
                                if biz_phone:
                                    wa_biz = whatsapp_link(
                                        biz_phone,
                                        "היי, אני בא לאסוף הזמנה של קבוצת רכישה מ-Kfar-Link."
                                    )
                                    st.markdown(f"📞 {biz_phone}")
                                    st.markdown(
                                        f"<a class='wa-btn' href='{wa_biz}' target='_blank'>💬 WhatsApp לעסק</a>",
                                        unsafe_allow_html=True,
                                    )

                    st.divider()

                    # ══════════════════════════════════════════════════
                    #  אזור 3: השוואת תרחישי מחיר
                    #
                    #  no_delivery = True → לא מציגים תרחיש A (משלוח חיצוני),
                    #  במקום זאת מציגים הודעת 'איסוף מהעסק בלבד'.
                    # ══════════════════════════════════════════════════
                    st.markdown("### 💰 השוואת מחירים")
                    is_no_delivery = deal.get("no_delivery", False)
                    sc_a, sc_b, sc_c = scenarios["A"], scenarios["B"], scenarios["C"]

                    hero_p      = sc_b.get("hero_price", 0)       # ברוטו = base_ppu
                    hero_net_p  = sc_b.get("hero_net_ppu", 0)     # נטו = אחרי קיזוז נסיעה
                    others_p    = sc_b.get("others_price", 0)
                    trip_pay    = sc_b.get("trip_payment", 0)      # כמה הגיבור מקבל על הנסיעה

                    # ── כרטיסי מחיר – כל כרטיס ב-st.markdown נפרד ──
                    # כרטיס הגיבור מציג: המחיר שהאחרים משלמים + תג "גיבור מקבל X₪"
                    def render_hero_scenario_card(others_price, trip_amount):
                        """כרטיס תרחיש גיבור – מחיר לאחרים + תג תשלום נסיעה לגיבור."""
                        trip_badge = (
                            f'<div style="margin-top:6px; font-size:0.7em; '
                            f'background:linear-gradient(135deg,#fff3cd,#ffeaa7); '
                            f'border-radius:8px; padding:3px 8px; color:#856404; font-weight:700;">'
                            f'🚗 גיבור מקבל {trip_amount}₪ על הנסיעה</div>'
                        )
                        html = (
                            f'<div style="background:#fff; border-radius:16px; padding:12px 10px; '
                            f'text-align:center; direction:rtl; border:1px solid #e0e0e0;">'
                            f'<div style="font-size:1.2em; margin-bottom:2px;">🦸</div>'
                            f'<div style="font-weight:600; color:#555; font-size:0.75em; '
                            f'line-height:1.2;">מחיר ליחידה<br>גיבור משלוחים</div>'
                            f'<div style="font-size:1.5em; font-weight:800; color:#17a2b8; '
                            f'margin:4px 0;">{others_price}₪</div>'
                            f'{trip_badge}</div>'
                        )
                        st.markdown(html, unsafe_allow_html=True)

                    if is_no_delivery:
                        card_col1, card_col2, card_col3 = st.columns(3)
                        with card_col1:
                            render_no_delivery_card_to_streamlit()
                        with card_col2:
                            render_hero_scenario_card(others_p, trip_pay)
                        with card_col3:
                            render_scenario_card_to_streamlit(
                                "💚", "מחיר ליחידה<br>מתנדב בחינם",
                                sc_c["price_per_unit"], "#28a745", star=True)
                    else:
                        card_col1, card_col2, card_col3 = st.columns(3)
                        with card_col1:
                            render_scenario_card_to_streamlit(
                                "🚚", "מחיר ליחידה<br>משלוח חיצוני",
                                sc_a["price_per_unit"], "#e67e22")
                        with card_col2:
                            render_hero_scenario_card(others_p, trip_pay)
                        with card_col3:
                            render_scenario_card_to_streamlit(
                                "💚", "מחיר ליחידה<br>מתנדב בחינם",
                                sc_c["price_per_unit"], "#28a745", star=True)

                    # ── אזהרת הוגנות: גיבור יקר ממשלוח חיצוני ──
                    if sc_b.get("hero_more_expensive") and not is_no_delivery:
                        st.warning("⚠️ **שים לב:** במצב זה משלוח חיצוני משתלם יותר לקבוצה מתרחיש גיבור משלוחים.")

                    st.divider()

                    # ══════════════════════════════════════════════════
                    #  אזור 4: ניהול מוביל
                    #
                    #  רק משתתף שכבר הזמין יחידות יכול להתנדב כמוביל.
                    #  היררכיה שנאכפת ברישום:
                    #  1. no_discount → מחליף תמיד את with_discount
                    #  2. with_discount → נכנס רק אם אין מוביל
                    # ══════════════════════════════════════════════════
                    st.markdown("### 🛺 מי מביא את ההזמנה?")

                    carrier         = deal.get("carrier")
                    vol_mode_key    = f"vol_mode_{deal['id']}"
                    cancel_mode_key = f"cancel_mode_{deal['id']}"

                    # בדיקה: האם המשתמש הנוכחי משתתף בעסקה?
                    cu_vol_check = st.session_state.get("current_user")
                    is_participant_for_vol = False
                    if cu_vol_check and deal["participants"]:
                        is_participant_for_vol = any(
                            p.get("phone", "").strip() == cu_vol_check["phone"].strip()
                            for p in deal["participants"]
                        )

                    # ── תצוגת מוביל נוכחי ──
                    if carrier:
                        is_free = carrier.get("type") == "no_discount"
                        c_bg    = "#d4edda" if is_free else "#d1ecf1"
                        c_border = "#28a745" if is_free else "#17a2b8"
                        c_text   = "#155724" if is_free else "#0c5460"
                        c_label  = "💚 מתנדב בחינם" if is_free else "🏄‍♂️ גיבור משלוחים (5% הנחה)"
                        biz_line = f"<br>🛺 לאסוף ב: {biz_addr}" if biz_addr else ""
                        wa_carrier = whatsapp_link(
                            carrier["phone"],
                            f"היי {carrier['name']}, אתה/את המוביל של קבוצת הרכישה '{deal['name']}' ב-Kfar-Link! 🙏"
                        )
                        st.markdown(
                            f"""
                            <div style="background:{c_bg};border-radius:10px;padding:14px;
                                        direction:rtl;border:2px solid {c_border};margin-bottom:10px;">
                                <span style="font-size:1em;font-weight:700;color:{c_text};">{c_label}</span><br>
                                <strong style="font-size:1.1em;">{carrier['name']}</strong>
                                &nbsp;·&nbsp; 📞 {carrier['phone']}
                                {biz_line}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"<a class='wa-btn' href='{wa_carrier}' target='_blank'>💬 WhatsApp למוביל</a>",
                            unsafe_allow_html=True,
                        )

                        # אם המוביל הוא 'עם הנחה' – משתתף בעסקה יכול להחליפו
                        if not is_free and is_participant_for_vol:
                            st.caption("💡 מוביל 'בחינם' יכול להחליפו ולהוריד את המחיר לכולם.")
                            if st.button(
                                "🟢 אני מתנדב להביא בחינם (ואחליף את המוביל הנוכחי)",
                                key=f"vol_free_override_{deal['id']}", use_container_width=True
                            ):
                                st.session_state[vol_mode_key] = "no_discount"
                                st.rerun()

                        # כפתור ביטול התנדבות – מוגן בטלפון
                        if st.button("↩️ בטל התנדבות", key=f"cancel_btn_{deal['id']}", type="secondary"):
                            st.session_state[cancel_mode_key] = True
                            st.rerun()

                        if st.session_state.get(cancel_mode_key):
                            # אימות מבוסס current_user – אין צורך להזין טלפון ידנית.
                            # רק המוביל הרשום יכול לבטל את עצמו.
                            cu_cancel = st.session_state.get("current_user")
                            if not cu_cancel:
                                st.warning("🔒 יש להזדהות ב-Sidebar כדי לבטל התנדבות.")
                            elif cu_cancel["phone"].strip() != carrier["phone"].strip():
                                st.error("🚫 רק המוביל הרשום יכול לבטל את עצמו.")
                            else:
                                with st.form(key=f"cancel_form_{deal['id']}"):
                                    st.warning(f"האם לבטל את ההתנדבות של **{carrier['name']}**?")
                                    cf1, cf2 = st.columns(2)
                                    do_cancel = cf1.form_submit_button("✅ אשר ביטול", type="primary", use_container_width=True)
                                    do_abort  = cf2.form_submit_button("❌ חזור", use_container_width=True)
                                    if do_cancel:
                                        st.session_state.bulk_deals[i]["carrier"] = None
                                        db.update_bulk_deal(st.session_state.bulk_deals[i])
                                        st.session_state.pop(cancel_mode_key, None)
                                        st.rerun()
                                    if do_abort:
                                        st.session_state.pop(cancel_mode_key, None)
                                        st.rerun()

                    else:
                        # אין מוביל
                        st.info("🛺 עדיין אין מי שיביא את ההזמנה מהעסק. היה הגיבור! 🏄‍♂️")
                        if is_participant_for_vol:
                            # רק משתתף שכבר הזמין יחידות יכול להתנדב
                            btn1, btn2 = st.columns(2)
                            if btn1.button(
                                "🟢 אני מתנדב להביא\n(בחינם)", key=f"vol_free_{deal['id']}",
                                use_container_width=True, type="primary"
                            ):
                                st.session_state[vol_mode_key] = "no_discount"
                                st.rerun()
                            if btn2.button(
                                "🏄‍♂️ גיבור משלוחים\n(+5% הנחה, עד 20₪)", key=f"vol_hero_{deal['id']}",
                                use_container_width=True
                            ):
                                st.session_state[vol_mode_key] = "with_discount"
                                st.rerun()
                        else:
                            st.caption("💡 כדי להתנדב כמוביל, יש קודם להצטרף לעסקה ולהזמין יחידות.")

                    # ── טופס רישום מוביל (נפתח אחרי לחיצה על כפתור, רק למשתתפים) ──
                    if st.session_state.get(vol_mode_key) and is_participant_for_vol:
                        vol_type = st.session_state[vol_mode_key]
                        type_str = (
                            "💚 מתנדב בחינם – הכי טוב לקבוצה! (מחיר C לכולם)"
                            if vol_type == "no_discount"
                            else (f"🏄‍♂️ גיבור משלוחים – {sc_b['others_price']}₪/יח' לאחרים | "
                                  f"אתה מקבל {sc_b['trip_payment']}₪ תשלום נסיעה | "
                                  f"נטו שלך: {sc_b['hero_net_ppu']}₪/יח'")
                        )
                        st.markdown(f"**{type_str}**")
                        # שם + טלפון נמשכים אוטומטית מהמשתמש המחובר
                        cu_carrier = st.session_state.get("current_user")
                        if not cu_carrier:
                            require_login("להתנדב כמוביל")
                            if st.button("❌ ביטול", key=f"vol_back_nologin_{deal['id']}"):
                                st.session_state.pop(vol_mode_key, None)
                                st.rerun()
                        else:
                            st.caption(f"📋 מתנדב/ת: **{cu_carrier['name']}** | 📞 {cu_carrier['phone']}")
                            with st.form(key=f"carrier_form_{deal['id']}"):
                                vs1, vs2 = st.columns(2)
                                v_confirm = vs1.form_submit_button("✅ אשר התנדבות", type="primary", use_container_width=True)
                                v_back    = vs2.form_submit_button("❌ ביטול", use_container_width=True)
                                if v_confirm:
                                    cur = deal.get("carrier")
                                    # כלל היררכיה: no_discount מחליף with_discount;
                                    # with_discount רק אם אין מוביל כלל
                                    can_reg = (
                                        not cur
                                        or vol_type == "no_discount"
                                        or cur.get("type") == "with_discount"
                                    )
                                    if can_reg:
                                        st.session_state.bulk_deals[i]["carrier"] = {
                                            "name":  cu_carrier["name"],
                                            "phone": cu_carrier["phone"],
                                            "type":  vol_type,
                                        }
                                        db.update_bulk_deal(st.session_state.bulk_deals[i])
                                        st.session_state.pop(vol_mode_key, None)
                                        st.rerun()
                                    else:
                                        st.error("כבר קיים מוביל 'בחינם'. לא ניתן להחליפו.")
                                if v_back:
                                    st.session_state.pop(vol_mode_key, None)
                                    st.rerun()

                    st.divider()

                    # ══════════════════════════════════════════════════
                    #  אזור 4.5: מחיר נוכחי ליחידה לפי אופי המשלוח
                    #
                    #  אופטימיזציה אוטומטית: אם הגיבור יקר ממשלוח חיצוני,
                    #  המערכת עוברת אוטומטית לתרחיש משלוח חיצוני.
                    # ══════════════════════════════════════════════════
                    carrier_now = deal.get("carrier")
                    auto_switched_to_delivery = False  # דגל: האם עברנו אוטומטית למשלוח

                    if carrier_now:
                        if carrier_now.get("type") == "no_discount":
                            # מתנדב בחינם – תמיד הכי טוב
                            active_price = sc_c["price_per_unit"]
                            active_label = "💚 מתנדב בחינם"
                            active_color = "#28a745"
                        elif sc_b.get("hero_more_expensive") and not is_no_delivery:
                            # גיבור יקר ממשלוח חיצוני → מעבר אוטומטי למשלוח
                            active_price = sc_a["price_per_unit"]
                            active_label = "🚚 משלוח חיצוני (אופטימיזציה)"
                            active_color = "#e67e22"
                            auto_switched_to_delivery = True
                        else:
                            # גיבור משלוחים רגיל
                            active_price = others_p
                            active_label = "🦸 גיבור משלוחים"
                            active_color = "#17a2b8"
                    elif is_no_delivery:
                        active_price = None
                        active_label = "🏪 ממתין למוביל"
                        active_color = "#f4511e"
                    else:
                        active_price = sc_a["price_per_unit"]
                        active_label = "🚚 משלוח חיצוני"
                        active_color = "#e67e22"

                    if active_price is not None:
                        st.markdown(
                            f'<div style="background:linear-gradient(135deg, #f0faf7, #F0FDFA); '
                            f'border-radius:16px; padding:14px; text-align:center; direction:rtl; '
                            f'border:2px solid {active_color}; margin:8px 0;">'
                            f'<div style="font-size:0.82em; color:#555; margin-bottom:4px;">'
                            f'💰 מחיר נוכחי ליחידה ({active_label})</div>'
                            f'<div style="font-size:2em; font-weight:800; color:{active_color};">'
                            f'{active_price}₪</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if auto_switched_to_delivery:
                            st.info("🔄 המערכת בחרה במשלוח חיצוני כיוון שהוא משתלם יותר לקבוצה מתרחיש גיבור.")
                    else:
                        st.warning("⏳ המחיר ייקבע ברגע שמוביל יירשם לעסקה")

                    st.divider()

                    # ══════════════════════════════════════════════════
                    #  אזור 5: פרטי מארגן + רשימת משתתפים
                    # ══════════════════════════════════════════════════
                    col_org, col_parts = st.columns([1, 2])

                    with col_org:
                        org_name  = deal.get("organizer_name", "—")
                        org_phone = deal.get("organizer_phone", "")
                        st.markdown("**👤 מארגן:**")
                        st.markdown(f"**{org_name}**")
                        if org_phone:
                            wa_org = whatsapp_link(
                                org_phone,
                                f"היי {org_name}, רוצה להצטרף לרכישה של '{deal['name']}' – מה הסכום לשלם?"
                            )
                            st.markdown(
                                f"📞 {org_phone}  \n"
                                f"<a class='wa-btn' href='{wa_org}' target='_blank'>💬 WhatsApp</a>",
                                unsafe_allow_html=True,
                            )
                        if box_is_full:
                            st.success("💳 שלח תשלום\nBit / Paybox")

                    with col_parts:
                        st.markdown(f"**👥 משתתפים ({len(deal['participants'])}):**")
                        if not deal["participants"]:
                            st.caption("אין משתתפים עדיין – הצטרף ראשון!")
                        else:
                            carrier_now_parts = deal.get("carrier")
                            carrier_phone = (carrier_now_parts or {}).get("phone", "")
                            carrier_type  = (carrier_now_parts or {}).get("type", "")
                            for p in deal["participants"]:
                                is_hero = (p.get("phone") == carrier_phone
                                           and carrier_phone
                                           and carrier_type == "with_discount")
                                carrier_badge = " 🚗" if p.get("phone") == carrier_phone and carrier_phone else ""
                                qty = p["quantity"]
                                # מחיר ליחידה: גיבור מקבל מחיר מיוחד,
                                # אלא אם המערכת עברה אוטומטית למשלוח חיצוני
                                if active_price is not None:
                                    if is_hero and not auto_switched_to_delivery:
                                        # ══ גיבור משלוחים ══
                                        # מציגים מחיר נטו (אחרי קיזוז תשלום נסיעה)
                                        # ומציינים כמה הוא מקבל על הנסיעה בנפרד
                                        p_price       = hero_net_p   # מחיר נטו ליחידה
                                        gross_total   = round(hero_p * qty, 2)
                                        net_total     = round(p_price * qty, 2)
                                        trip_received = trip_pay      # תשלום נסיעה שמקבל
                                        st.markdown(
                                            f"• **{p['name']}**{carrier_badge} – "
                                            f"{qty} יח' | {p_price}₪ ליחידה (נטו) | "
                                            f"סה\"כ לתשלום: **{net_total}₪** "
                                            f"*(כולל {trip_received}₪ תשלום נסיעה שמקבל)*"
                                        )
                                    else:
                                        # ══ משתתף רגיל ══
                                        p_price = active_price
                                        p_total = round(p_price * qty, 2)
                                        st.markdown(
                                            f"• **{p['name']}**{carrier_badge} – "
                                            f"{qty} יח' | {p_price}₪ ליחידה | "
                                            f"סה\"כ לתשלום: **{p_total}₪**"
                                        )
                                else:
                                    st.markdown(
                                        f"• **{p['name']}**{carrier_badge} – "
                                        f"{qty} יח' | ⏳ ממתין למחיר"
                                    )

                        # ── עדכון כמות / יציאה מעסקה למשתתפים קיימים ──
                        # מוצג למשתמש מחובר שכבר נמצא ברשימה – גם כשהארגז מלא (closed)
                        if deal_status["code"] in ("conditional", "closed") and deal["participants"]:
                            cu_upd = st.session_state.get("current_user")
                            # מחפשים את המשתמש המחובר ברשימת המשתתפים
                            p_idx = None
                            if cu_upd:
                                p_idx = next(
                                    (idx for idx, p in enumerate(deal["participants"])
                                     if p.get("phone", "").strip() == cu_upd["phone"].strip()),
                                    None
                                )
                            # מציגים כפתורים רק אם המשתמש אכן משתתף
                            if cu_upd and p_idx is not None:
                                upd_key   = f"upd_qty_{deal['id']}"
                                leave_key = f"leave_deal_{deal['id']}"
                                btn_upd_col, btn_leave_col = st.columns(2)
                                with btn_upd_col:
                                    if st.button(
                                        "✏️ עדכן כמות",
                                        key=f"upd_btn_{deal['id']}", type="secondary",
                                        use_container_width=True
                                    ):
                                        st.session_state[upd_key] = True
                                        st.session_state.pop(leave_key, None)
                                with btn_leave_col:
                                    if st.button(
                                        "🚪 יציאה מעסקה",
                                        key=f"leave_btn_{deal['id']}", type="secondary",
                                        use_container_width=True
                                    ):
                                        st.session_state[leave_key] = True
                                        st.session_state.pop(upd_key, None)

                                # ── טופס עדכון כמות ──
                                if st.session_state.get(upd_key):
                                    current_qty = deal["participants"][p_idx]["quantity"]
                                    with st.form(key=f"upd_form_{deal['id']}"):
                                        new_qty = st.number_input(
                                            "כמות יחידות חדשה", min_value=1, max_value=50, value=current_qty,
                                            key=f"uqt_{deal['id']}"
                                        )
                                        ua, ub = st.columns(2)
                                        u_confirm = ua.form_submit_button("✅ עדכן", type="primary", use_container_width=True)
                                        u_cancel  = ub.form_submit_button("❌ ביטול", use_container_width=True)
                                        if u_confirm:
                                            st.session_state.bulk_deals[i]["participants"][p_idx]["quantity"] = int(new_qty)
                                            db.update_bulk_deal(st.session_state.bulk_deals[i])
                                            st.session_state.pop(upd_key, None)
                                            st.rerun()
                                        if u_cancel:
                                            st.session_state.pop(upd_key, None)
                                            st.rerun()

                                # ── טופס יציאה מעסקה ──
                                if st.session_state.get(leave_key):
                                    p_name = deal["participants"][p_idx]["name"]
                                    with st.form(key=f"leave_form_{deal['id']}"):
                                        st.warning(f"האם אתה בטוח שברצונך לצאת מהעסקה, **{p_name}**?")
                                        lf1, lf2 = st.columns(2)
                                        do_leave = lf1.form_submit_button("✅ כן, צא מהעסקה", type="primary", use_container_width=True)
                                        no_leave = lf2.form_submit_button("❌ ביטול", use_container_width=True)
                                        if do_leave:
                                            # הסרת המשתתף מהרשימה
                                            st.session_state.bulk_deals[i]["participants"].pop(p_idx)
                                            # אם המשתתף היה גם המוביל – מבטלים גם את המוביל
                                            cur_carrier = deal.get("carrier")
                                            if cur_carrier and cur_carrier.get("phone", "").strip() == cu_upd["phone"].strip():
                                                st.session_state.bulk_deals[i]["carrier"] = None
                                            db.update_bulk_deal(st.session_state.bulk_deals[i])
                                            st.session_state.pop(leave_key, None)
                                            st.success(f"👋 {p_name} יצא/ה מהעסקה.")
                                            st.rerun()
                                        if no_leave:
                                            st.session_state.pop(leave_key, None)
                                            st.rerun()

                    st.divider()

                    # ══════════════════════════════════════════════════
                    #  אזור 6: טופס הצטרפות – קנייה בלבד (נקי)
                    # ══════════════════════════════════════════════════
                    # שומרים על עסקה פתוחה רק כשהיא "מותנית" או "ריקה"
                    # (לא כשסגורה להזמנה, ולא כשבוטלה)
                    if deal_status["code"] in ("conditional", "empty"):
                        # בדיקה: האם המשתמש המחובר כבר בעסקה?
                        cu_join = st.session_state.get("current_user")
                        already_in_deal = False
                        if cu_join:
                            existing_phones = [p.get("phone","").strip() for p in deal["participants"]]
                            already_in_deal = cu_join["phone"].strip() in existing_phones

                        if already_in_deal:
                            # המשתמש כבר בעסקה – לא מציגים טופס הצטרפות
                            st.info(f"✅ **{cu_join['name']}**, את/ה כבר בעסקה הזו. השתמש/י בכפתורי 'עדכן כמות' או 'יציאה מעסקה' למעלה.")
                        else:
                            st.markdown("**🙋 הצטרף לעסקה:**")
                            if not require_login("להצטרף לעסקה"):
                                pass  # require_login כבר הציג הודעה
                            else:
                                st.caption(f"👤 מצטרף כ: **{cu_join['name']}** | 📞 {cu_join['phone']}")
                                with st.form(key=f"join_{deal['id']}"):
                                    j_qty = st.number_input(
                                        "כמות יחידות", min_value=1, max_value=50, value=1,
                                        key=f"jq_{deal['id']}"
                                    )
                                    submitted = st.form_submit_button("הצטרף לעסקה 🚀", use_container_width=True)
                                    if submitted:
                                        # need_expiry = תאריך יעד העסקה (אוטומטי, לא ידני)
                                        auto_expiry = deal.get("target_date", (date.today() + timedelta(days=14)).isoformat())
                                        existing = st.session_state.bulk_deals[i].setdefault("participants", []) or []
                                        existing.append({
                                            "id":          gen_id(),
                                            "name":        cu_join["name"],
                                            "phone":       cu_join["phone"],
                                            "quantity":    int(j_qty),
                                            "need_expiry": auto_expiry,
                                        })
                                        st.session_state.bulk_deals[i]["participants"] = existing
                                        db.update_bulk_deal(st.session_state.bulk_deals[i])
                                        st.success(f"✅ {cu_join['name']} הצטרף לעסקה!")
                                        st.rerun()
                    elif deal_status["code"] == "closed":
                        # הודעה למשתתף – מה עליו לעשות עכשיו
                        org_name  = deal.get("organizer_name", "המארגן")
                        org_phone = deal.get("organizer_phone", "")
                        wa_pay = whatsapp_link(
                            org_phone,
                            f"היי {org_name}! אני מוכן/ה לשלם על ההזמנה של '{deal['name']}' 💰"
                        ) if org_phone else ""
                        pay_btn = f"&nbsp; <a class='wa-btn' href='{wa_pay}' target='_blank'>💬 שלח ל-{org_name}</a>" if wa_pay else ""
                        st.markdown(
                            f"""
                            <div style="background:#d4edda;border-radius:10px;padding:14px 18px;
                                        direction:rtl;border:1px solid #28a745;margin-bottom:8px;">
                                🎉 <strong>הארגז מלא!</strong> העסקה סגורה להצטרפויות חדשות.<br>
                                💳 שלחו תשלום של <strong>{target_p}₪ ליחידה</strong>
                                ל-<strong>{org_name}</strong> דרך Bit / Paybox.
                                {pay_btn}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    elif deal_status["code"] == "cancelled":
                        st.error(
                            "🔴 **העסקה בוטלה.** הדדליין עבר לפני שהארגז התמלא.  \n"
                            "המארגן יכול להאריך את הדדליין ולהחיות את העסקה."
                        )

                    st.divider()

                    # ══════════════════════════════════════════════════
                    #  אזור 7: מערכת תגובות (שאלות ותשובות)
                    # ══════════════════════════════════════════════════
                    st.markdown("**💬 שאלות ותגובות:**")

                    # הצגת תגובות קיימות
                    comments = deal.get("comments", [])
                    if not comments:
                        st.caption("אין תגובות עדיין. שאל/י ראשון/ה!")
                    else:
                        for cmt in comments:
                            ts = cmt.get("created_at", "")[:16].replace("T", " ")
                            st.markdown(
                                f"""
                                <div style="background:#f8f9fa;border-radius:8px;padding:8px 12px;
                                            margin-bottom:6px;direction:rtl;border-right:3px solid #dee2e6;">
                                    <strong style="color:#333;">{cmt['author']}</strong>
                                    <span style="color:#aaa;font-size:0.78em;margin-right:8px;">{ts}</span><br>
                                    <span style="color:#555;">{cmt['text']}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    # טופס הוספת תגובה – שם הכותב נמשך אוטומטית מה-current_user
                    cu_cmt = st.session_state.get("current_user")
                    if not require_login("להוסיף תגובה"):
                        pass  # require_login הציג הודעה
                    else:
                        with st.form(key=f"cmt_form_{deal['id']}"):
                            cmt_text = st.text_input("תגובה / שאלה *", key=f"cmt_t_{deal['id']}")
                            if st.form_submit_button("שלח תגובה 💬", use_container_width=True):
                                if cmt_text:
                                    new_cmt = {
                                        "id":         gen_id(),
                                        "author":     cu_cmt["name"],
                                        "text":       cmt_text.strip(),
                                        "created_at": datetime.now().isoformat(),
                                    }
                                    existing_cmts = st.session_state.bulk_deals[i].get("comments") or []
                                    existing_cmts.append(new_cmt)
                                    st.session_state.bulk_deals[i]["comments"] = existing_cmts
                                    db.update_bulk_deal(st.session_state.bulk_deals[i])
                                    st.rerun()
                                else:
                                    st.error("נא למלא תגובה.")

                # ── מרווח בין כרטיסי עסקאות ──
                st.markdown('<div style="margin-bottom:24px;"></div>', unsafe_allow_html=True)

    # ── טאב: הצעת עסקה חדשה ──────────────────────────────────
    with tab_new:
        st.markdown("### פרסם עסקת קבוצה חדשה")
        # בלוק זה חסום למשתמשים שלא הזדהו
        cu_new_deal = st.session_state.get("current_user")
        if not require_login("לפרסם עסקה חדשה"):
            pass  # require_login הציג הודעה
        else:
            st.caption(f"📋 מארגן: **{cu_new_deal['name']}** | 📞 {cu_new_deal['phone']}")
            with st.form("new_deal_form"):
                # ── פרטי המוצר ──
                st.markdown("**📦 פרטי המוצר:**")
                nc1, nc2, nc_emoji = st.columns([2, 2, 1])
                d_name     = nc1.text_input("שם המוצר *", placeholder="שמן זית, נייר A4...")
                d_supplier = nc2.text_input("שם העסק / ספק *", placeholder="מכולת שמואל...")
                d_emoji    = nc_emoji.text_input("אימוג'י מוצר", value="📦", help="בחר אימוג'י שמייצג את המוצר")

                nc3, nc4, nc5 = st.columns(3)
                d_retail    = nc3.number_input("מחיר קמעונאי (₪/יחידה)", min_value=1.0, value=30.0, step=0.5)
                d_box_price = nc4.number_input("מחיר ארגז מהספק (₪)",    min_value=1.0, value=100.0, step=5.0)
                d_box_size  = nc5.number_input("יחידות בארגז",            min_value=1,   value=6,    step=1)

                st.caption(
                    f"💡 מחיר ספק ליחידה: **{d_box_price / d_box_size:.2f}₪** "
                    f"לעומת קמעונאי {d_retail}₪ — "
                    f"חיסכון פוטנציאלי: {max(0, (d_retail - d_box_price/d_box_size)/d_retail*100):.1f}%"
                )

                st.divider()

                # ── פרטי העסק – למתנדב שמגיע לאסוף ──
                st.markdown("**🏪 פרטי העסק (למתנדב שמגיע לאסוף):**")
                ba1, ba2 = st.columns(2)
                d_biz_addr  = ba1.text_input("כתובת העסק", placeholder="רחוב הרצל 5, תל אביב")
                d_biz_hours = ba2.text_input("שעות פתיחה", placeholder="א'–ו' 08:00–20:00")

                d_biz_phone = st.text_input("טלפון העסק", placeholder="03-1234567")

                # ── Checkbox: אין משלוח חיצוני ──
                # אם מסומן, שדה עלות המשלוח נעלם, ותרחיש A לא יוצג.
                d_no_delivery = st.checkbox(
                    "🚫 אין אפשרות למשלוח חיצוני מהעסק (איסוף עצמי בלבד)",
                    value=False,
                )
                if d_no_delivery:
                    d_delivery_cost = 0.0
                    st.caption("📌 העסקה דורשת מתנדב שיאסוף מהעסק. לא יוצג תרחיש משלוח חיצוני.")
                else:
                    d_delivery_cost = st.number_input(
                        "עלות משלוח חיצוני (₪)",
                        min_value=0.0, value=25.0, step=5.0,
                        help="כמה עולה להזמין שליח מהעסק לכפר?"
                    )

                st.divider()

                # ── תאריך יעד ──
                st.markdown("**📅 תאריך יעד:**")
                d_target_date = st.date_input(
                    "מתי צריכים שהמוצרים יגיעו לכפר? *",
                    min_value=date.today() + timedelta(days=1),
                    value=date.today() + timedelta(days=7),
                    help="תאריך זה מוצג לכל המשתתפים כדי לתאם ציפיות."
                )

                st.divider()

                # ── הצטרפות ראשונה – כמות בלבד (שם+טלפון מ-current_user, תפוגה = תאריך יעד) ──
                st.markdown("**🛒 ההזמנה שלי:**")
                d_my_qty = st.number_input("כמות יחידות שלי", min_value=1, value=1)

                st.caption("💡 רוצה להתנדב כמוביל? תוכל לעשות זאת ישירות מכרטיס העסקה לאחר פרסום.")

                submit_deal = st.form_submit_button("📢 פרסם עסקה", use_container_width=True, type="primary")
                if submit_deal:
                    if not d_name or not d_supplier:
                        st.error("נא למלא את כל השדות המסומנים ב-*.")
                    elif d_box_price / d_box_size >= d_retail:
                        st.warning("⚠️ מחיר הספק ליחידה גבוה ממחיר הקמעונאי. האם זו עסקה כדאית?")
                    else:
                        new_deal = {
                            "id":              gen_id(),
                            "product_emoji":   d_emoji.strip() or "📦",
                            "name":            d_name,
                            "supplier":        d_supplier,
                            "price_retail":    d_retail,
                            "box_size":        int(d_box_size),
                            "price_per_box":   d_box_price,
                            "business_address": d_biz_addr,
                            "business_hours":   d_biz_hours,
                            "business_phone":   d_biz_phone,
                            "delivery_cost":    d_delivery_cost,
                            # no_delivery: אם True, אין אפשרות משלוח – איסוף עצמי בלבד.
                            # משפיע על תצוגת תרחישי מחיר (תרחיש A לא מוצג).
                            "no_delivery":      d_no_delivery,
                            "target_date":      d_target_date.isoformat(),
                            "created_at":       datetime.now().isoformat(),
                            "status":           "open",
                            # המארגן = המשתמש המחובר
                            "organizer_name":   cu_new_deal["name"],
                            "organizer_phone":  cu_new_deal["phone"],
                            "carrier":  None,   # ייקבע מכפתורי ההובלה בכרטיס העסקה
                            "comments": [],    # מערכת שאלות ותשובות
                            "participants": [{
                                "id":          gen_id(),
                                "name":        cu_new_deal["name"],
                                "phone":       cu_new_deal["phone"],
                                "quantity":    d_my_qty,
                                # תפוגת צורך = תאריך יעד העסקה (אוטומטי)
                                "need_expiry": d_target_date.isoformat(),
                            }],
                        }
                        db.add_bulk_deal(new_deal)
                        st.success(f"🎉 עסקת '{d_name}' פורסמה! שתף את השכנים.")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  מודול 2 – השאלת ציוד (Share Board)
# ═══════════════════════════════════════════════════════════════════

def show_share_board():
    """לוח השאלת ציוד – מציע/מחפש עם לינקים ל-WhatsApp."""
    st.title("🔧 השאלת ציוד")
    st.caption("שתף ציוד עם השכנים שלך. חוסך כסף, מחזק קהילה.")

    tab_all, tab_offer, tab_seek = st.tabs(
        ["🗂️ כל הפריטים", "📦 הצע ציוד", "🔍 חפש ציוד"]
    )

    def render_item_card(item: dict):
        """מרנדר כרטיס פריט אחד עם כפתור WhatsApp + מחיקה למפרסם."""
        type_label = "מציע" if item["type"] == "offer" else "מחפש"
        badge_class = "badge-offer" if item["type"] == "offer" else "badge-seek"
        card_class = "kf-card-offer" if item["type"] == "offer" else "kf-card-seek"
        emoji = "📦" if item["type"] == "offer" else "🔍"

        wa_text = (
            f"היי {item['owner_name']}, ראיתי בKfar-Link שאת/ה {type_label} '{item['item_name']}'. "
            f"אשמח לדבר!"
        )
        wa_url = whatsapp_link(item["phone"], wa_text)

        st.markdown(
            f"""
            <div class="kf-card {card_class}">
                <span class="kf-badge {badge_class}">{emoji} {type_label}</span>
                <strong style="font-size:1.1em">{item['item_name']}</strong><br>
                <span style="color:#555; font-size:0.9em">{item['description']}</span><br><br>
                <strong>👤 {item['owner_name']}</strong> &nbsp;
                <a class="wa-btn" href="{wa_url}" target="_blank">💬 WhatsApp</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # כפתור מחיקה – מוגבל למפרסם בלבד (לפי טלפון)
        cu_share = st.session_state.get("current_user")
        is_item_owner = (
            cu_share
            and cu_share["phone"].strip() == item.get("phone", "").strip()
        )
        if is_item_owner:
            if st.button("🗑️ מחק פריט", key=f"del_share_{item['id']}", type="secondary"):
                db.delete_share_item(item["id"])
                st.rerun()

    # ── טאב: כל הפריטים ──
    with tab_all:
        offers = [i for i in st.session_state.share_items if i["type"] == "offer"]
        seeks = [i for i in st.session_state.share_items if i["type"] == "seek"]

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"### 📦 מציעים ({len(offers)})")
            if not offers:
                st.info("אין הצעות כרגע.")
            for item in offers:
                render_item_card(item)

        with col_b:
            st.markdown(f"### 🔍 מחפשים ({len(seeks)})")
            if not seeks:
                st.info("אין בקשות כרגע.")
            for item in seeks:
                render_item_card(item)

    # ── טאב: הצע ציוד ──
    with tab_offer:
        st.markdown("### הצע פריט להשאלה")
        cu_offer = st.session_state.get("current_user")
        if not require_login("לפרסם הצעת ציוד"):
            pass
        else:
            st.caption(f"📋 מוצג כ: **{cu_offer['name']}** | 📞 {cu_offer['phone']}")
            with st.form("offer_form"):
                o_item = st.text_input("שם הפריט *", placeholder="מקדחה, סולם, עגלת קניות...")
                o_desc = st.text_area("תיאור קצר", placeholder="מצב, זמינות, תנאים...", height=80)
                if st.form_submit_button("📢 פרסם הצעה", use_container_width=True, type="primary"):
                    if not o_item:
                        st.error("נא למלא את שם הפריט.")
                    else:
                        db.add_share_item({
                            "id": gen_id(), "type": "offer",
                            "item_name": o_item, "description": o_desc,
                            "owner_name": cu_offer["name"], "phone": cu_offer["phone"],
                            "created_at": datetime.now().isoformat(),
                        })
                        st.success(f"✅ הפריט '{o_item}' פורסם!")
                        st.rerun()

    # ── טאב: חפש ציוד ──
    with tab_seek:
        st.markdown("### פרסם בקשה לציוד")
        cu_seek = st.session_state.get("current_user")
        if not require_login("לפרסם בקשת ציוד"):
            pass
        else:
            st.caption(f"📋 מוצג כ: **{cu_seek['name']}** | 📞 {cu_seek['phone']}")
            with st.form("seek_form"):
                s_item = st.text_input("מה אתה מחפש? *", placeholder="כיסא נוסף, מזגן נייד...")
                s_desc = st.text_area("תיאור קצר", placeholder="למה אתה צריך, לכמה זמן...", height=80)
                if st.form_submit_button("🔍 פרסם בקשה", use_container_width=True, type="primary"):
                    if not s_item:
                        st.error("נא למלא את שם הפריט.")
                    else:
                        db.add_share_item({
                            "id": gen_id(), "type": "seek",
                            "item_name": s_item, "description": s_desc,
                            "owner_name": cu_seek["name"], "phone": cu_seek["phone"],
                            "created_at": datetime.now().isoformat(),
                        })
                        st.success(f"✅ הבקשה ל'{s_item}' פורסמה!")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  מודול 3 – עבודות מזדמנות (Gig Jobs)
# ═══════════════════════════════════════════════════════════════════

def show_gig_jobs():
    """לוח עבודות מזדמנות עם שכר וסטטוס."""
    st.title("💼 עבודות מזדמנות")
    st.caption("עבודות קטנות בתוך הקהילה – עזרה הדדית בתמורה הוגנת. 🐱")

    tab_view, tab_post = st.tabs(["📋 משרות פתוחות", "➕ פרסם עבודה"])

    STATUS_MAP = {
        "open": ("🟢 פתוח", "badge-open"),
        "taken": ("🟡 תפוס", "badge-taken"),
        "done": ("⚫ הושלם", "badge-done"),
    }
    WAGE_TYPE_MAP = {"per_hour": "₪/שעה", "fixed": "₪ (מחיר קבוע)"}

    with tab_view:
        # סינון לפי סטטוס
        filter_status = st.radio(
            "הצג:", ["פתוחות בלבד", "הכל"],
            horizontal=True, index=0, label_visibility="collapsed"
        )
        jobs = st.session_state.gig_jobs
        if filter_status == "פתוחות בלבד":
            jobs = [j for j in jobs if j["status"] == "open"]

        if not jobs:
            st.info("אין משרות פתוחות כרגע.")
        else:
            for idx, job in enumerate(st.session_state.gig_jobs):
                if filter_status == "פתוחות בלבד" and job["status"] != "open":
                    continue

                status_label, status_badge = STATUS_MAP.get(job["status"], ("?", ""))
                wage_label = WAGE_TYPE_MAP.get(job["wage_type"], "")
                wa_text = f"היי {job['poster_name']}, ראיתי בKfar-Link את המשרה: '{job['title']}'. אני מעוניין!"
                wa_url = whatsapp_link(job["phone"], wa_text)

                st.markdown(
                    f"""
                    <div class="kf-card kf-card-job">
                        <span class="kf-badge {status_badge}">{status_label}</span>
                        <strong style="font-size:1.1em">{job['title']}</strong><br>
                        <span style="color:#555; font-size:0.9em">{job['description']}</span><br><br>
                        💰 <strong>{job['wage']}{wage_label}</strong> &nbsp;|&nbsp;
                        👤 {job['poster_name']} &nbsp;
                        <a class="wa-btn" href="{wa_url}" target="_blank">💬 WhatsApp</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # עדכון סטטוס + מחיקה – מוגבל למפרסם בלבד (לפי טלפון)
                real_idx = st.session_state.gig_jobs.index(job)
                cu_gig_view = st.session_state.get("current_user")
                is_poster = (
                    cu_gig_view
                    and cu_gig_view["phone"].strip() == job.get("phone", "").strip()
                )
                if is_poster:
                    gcol1, gcol2 = st.columns([3, 1])
                    with gcol1:
                        new_status = st.selectbox(
                            f"סטטוס עבודה #{real_idx + 1}",
                            options=["open", "taken", "done"],
                            index=["open", "taken", "done"].index(job["status"]),
                            format_func=lambda s: STATUS_MAP[s][0],
                            key=f"status_{job['id']}",
                            label_visibility="collapsed",
                        )
                        if new_status != job["status"]:
                            updated_job = dict(st.session_state.gig_jobs[real_idx])
                            updated_job["status"] = new_status
                            db.update_gig_job(updated_job)
                            st.rerun()
                    with gcol2:
                        if st.button("🗑️ מחק", key=f"del_job_{job['id']}", type="secondary"):
                            db.delete_gig_job(job["id"])
                            st.rerun()

    with tab_post:
        st.markdown("### פרסם עבודה חדשה")
        # שם + טלפון נמשכים מה-current_user – אין צורך בשדות ידניים
        cu_gig = st.session_state.get("current_user")
        if not require_login("לפרסם עבודה חדשה"):
            pass
        else:
            st.caption(f"📋 מפרסם: **{cu_gig['name']}** | 📞 {cu_gig['phone']}")
            with st.form("gig_form"):
                g_title = st.text_input("כותרת העבודה *", placeholder="עזרה בהובלה, שמירה על חיה...")
                g_desc = st.text_area("תיאור מפורט", placeholder="מה צריך לעשות, מתי, כמה זמן...", height=80)
                gc1, gc2 = st.columns(2)
                g_wage = gc1.number_input("שכר (₪) *", min_value=0.0, value=50.0, step=5.0)
                g_wage_type = gc2.selectbox("סוג שכר", ["per_hour", "fixed"],
                                            format_func=lambda x: WAGE_TYPE_MAP[x])
                if st.form_submit_button("📢 פרסם עבודה", use_container_width=True, type="primary"):
                    if not g_title:
                        st.error("נא למלא כותרת.")
                    else:
                        db.add_gig_job({
                            "id": gen_id(), "title": g_title, "description": g_desc,
                            "wage": g_wage, "wage_type": g_wage_type,
                            "status": "open",
                            "poster_name": cu_gig["name"], "phone": cu_gig["phone"],
                            "created_at": datetime.now().isoformat(),
                        })
                        st.success(f"✅ העבודה '{g_title}' פורסמה!")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  מודול 4 – פעילויות וטרמפים (Activities & Rides)
# ═══════════════════════════════════════════════════════════════════

def show_activities():
    """לוח פעילויות, טרמפים ובקשות עזרה הדדית."""
    st.title("🗓️ פעילויות ועזרה הדדית")
    st.caption("מה קורה בכפר? הצטרף לפעילות, הצע טרמפ, או בקש עזרה מהשכנים.")

    # מאפשר קפיצה מהפיד לפריט ספציפי (anchor לאחר rerun)
    focus_id = st.session_state.pop("_activity_focus", None)

    tab_view, tab_post = st.tabs(["📋 פעילויות קרובות", "➕ פרסם פעילות / טרמפ / בקשת עזרה"])

    with tab_view:
        # מיון לפי תאריך האירוע (מוקדם → מאוחר)
        sorted_acts = sorted(
            st.session_state.activities,
            key=lambda a: a["event_date"]
        )

        if not sorted_acts:
            st.info("אין פעילויות מתוכננות. הוסף משהו!")
        else:
            for act in sorted_acts:
                a_type = act.get("type", "activity")
                is_help = a_type == "help_request"

                # עבור בקשת עזרה אין מגבלת מקומות — כל מי שרוצה יכול להתנדב
                if is_help:
                    volunteers = act.get("volunteers", [])
                    vol_count = len(volunteers)
                    type_icon = "🆘"
                    type_label = "בקשת עזרה"
                    card_class = "kf-card-help"
                    badge_class = "badge-help"
                else:
                    seats_taken = len(act["participants"])
                    seats_left = act["total_seats"] - seats_taken
                    is_full = seats_left <= 0
                    type_icon = "🚗" if a_type == "ride" else "🎉"
                    type_label = "טרמפ" if a_type == "ride" else "פעילות"
                    card_class = "kf-card-activity"
                    badge_class = "badge-open"

                date_str = act["event_date"]
                location_html = f"&nbsp; 📍 {act['location']}" if act.get("location") else ""

                with st.container():
                    # עוגן לגלילה אוטומטית מהפיד
                    if focus_id == act["id"]:
                        st.markdown(f"<div id='act_{act['id']}'></div>", unsafe_allow_html=True)
                        st.markdown(
                            "<script>window.location.hash='act_" + act['id'] + "';</script>",
                            unsafe_allow_html=True,
                        )

                    if is_help:
                        meta_line = f"🙋 מתנדבים: <strong>{vol_count}</strong>"
                    else:
                        total_seats_val = act["total_seats"]
                        if is_full:
                            seats_text = "מלא ❌"
                        else:
                            seats_text = f"{seats_left} פנויים מתוך {total_seats_val}"
                        meta_line = f"🪑 מקומות: <strong>{seats_text}</strong>"

                    st.markdown(
                        f"""
                        <div class="kf-card {card_class}">
                            {type_icon} <span class="kf-badge {badge_class}">{type_label}</span>
                            <strong style="font-size:1.1em">{act['title']}</strong><br>
                            <span style="color:#555; font-size:0.9em">{act['description']}</span><br><br>
                            📅 {date_str} &nbsp; ⏰ {act['event_time']}{location_html}<br>
                            👤 מפרסם: {act['organizer_name']} &nbsp;
                            {meta_line}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # ── פירוט מתנדבים / משתתפים ──
                    if is_help:
                        if act.get("volunteers"):
                            with st.expander(f"🙋 מתנדבים ({vol_count})"):
                                for v in act["volunteers"]:
                                    wa = whatsapp_link(
                                        v["phone"],
                                        f"היי {v['name']}, ראיתי שהתנדבת לעזור ב'{act['title']}'. תודה! 🙏"
                                    )
                                    st.markdown(
                                        f"• {v['name']} ({v['phone']}) &nbsp; "
                                        f"<a href='{wa}' target='_blank' class='wa-btn'>💬 וואטסאפ</a>",
                                        unsafe_allow_html=True,
                                    )
                    else:
                        if act["participants"]:
                            with st.expander(f"👥 משתתפים ({seats_taken})"):
                                for p in act["participants"]:
                                    st.markdown(f"• {p['name']} ({p['phone']})")

                    # ── הרשאות: מחיקת פעילות (מפרסם בלבד) ──
                    cu_act_view = st.session_state.get("current_user")
                    is_act_owner = (
                        cu_act_view
                        and cu_act_view["phone"].strip() == act.get("phone", "").strip()
                    )
                    if is_act_owner:
                        orig_idx_del = next(
                            (i for i, a in enumerate(st.session_state.activities) if a["id"] == act["id"]), None
                        )
                        if orig_idx_del is not None:
                            if st.button("🗑️ מחק", key=f"del_act_{act['id']}", type="secondary"):
                                db.delete_activity(act["id"])
                                st.rerun()

                    # ── הצטרפות / התנדבות ──
                    if is_help:
                        # ליצור קשר ישיר עם המבקש + רישום כמתנדב
                        wa_organizer = whatsapp_link(
                            act["phone"],
                            f"היי {act['organizer_name']}, ראיתי את הבקשה שלך '{act['title']}' ואשמח לעזור 🙏"
                        )
                        st.markdown(
                            f"<a href='{wa_organizer}' target='_blank' class='wa-btn'>💬 דבר/י עם {act['organizer_name']}</a>",
                            unsafe_allow_html=True,
                        )
                        st.markdown("")  # רווח

                        with st.expander("🙋 אני רוצה לעזור"):
                            cu_vol = st.session_state.get("current_user")
                            if not require_login("להירשם כמתנדב/ת"):
                                pass
                            elif cu_vol["phone"].strip() == act["phone"].strip():
                                st.caption("זו הבקשה שלך 🙂")
                            else:
                                st.caption(f"👤 מתנדב/ת כ: **{cu_vol['name']}** | 📞 {cu_vol['phone']}")
                                with st.form(key=f"vol_{act['id']}"):
                                    if st.form_submit_button("🤝 סמן אותי כמעוניין/ת לעזור", use_container_width=True):
                                        orig_idx = next(
                                            i for i, a in enumerate(st.session_state.activities)
                                            if a["id"] == act["id"]
                                        )
                                        updated_act = st.session_state.activities[orig_idx]
                                        vol_list = updated_act.setdefault("volunteers", []) or []
                                        if any(v["phone"].strip() == cu_vol["phone"].strip() for v in vol_list):
                                            st.warning("כבר סימנת שאתה מעוניין/ת לעזור!")
                                        else:
                                            vol_list.append(
                                                {"name": cu_vol["name"], "phone": cu_vol["phone"]}
                                            )
                                            updated_act["volunteers"] = vol_list
                                            db.update_activity(updated_act)
                                            st.success(f"🙏 תודה {cu_vol['name']}! {act['organizer_name']} יוכל/תוכל ליצור איתך קשר.")
                                            st.rerun()
                    else:
                        if not is_full:
                            with st.expander("🙋 הצטרף!"):
                                cu_join_act = st.session_state.get("current_user")
                                if not require_login("להצטרף לפעילות"):
                                    pass
                                else:
                                    st.caption(f"👤 מצטרף כ: **{cu_join_act['name']}** | 📞 {cu_join_act['phone']}")
                                    with st.form(key=f"join_act_{act['id']}"):
                                        if st.form_submit_button("הצטרף ✅", use_container_width=True):
                                            if any(p["phone"].strip() == cu_join_act["phone"].strip() for p in act["participants"]):
                                                st.warning("נראה שכבר נרשמת!")
                                            else:
                                                orig_idx = next(
                                                    i for i, a in enumerate(st.session_state.activities)
                                                    if a["id"] == act["id"]
                                                )
                                                updated_act = st.session_state.activities[orig_idx]
                                                updated_act.setdefault("participants", []).append(
                                                    {"name": cu_join_act["name"], "phone": cu_join_act["phone"]}
                                                )
                                                db.update_activity(updated_act)
                                                st.success(f"🎉 {cu_join_act['name']} הצטרף ל'{act['title']}'!")
                                                st.rerun()
                        else:
                            st.warning("❌ כל המקומות תפוסים.")

                    st.markdown("---")

    with tab_post:
        st.markdown("### פרסם פעילות / טרמפ / בקשת עזרה")
        cu_post_act = st.session_state.get("current_user")
        if not require_login("לפרסם"):
            pass
        else:
            st.caption(f"📋 מפרסם/ת: **{cu_post_act['name']}** | 📞 {cu_post_act['phone']}")

            # בחירת סוג מחוץ לטופס כדי לאפשר רינדור מותנה של שדות (מקומות/מיקום מוסתרים בבקשת עזרה)
            p_type = st.radio(
                "סוג:",
                ["activity", "ride", "help_request"],
                format_func=lambda x: {
                    "activity": "🎉 פעילות",
                    "ride": "🚗 טרמפ",
                    "help_request": "🆘 בקשת עזרה",
                }[x],
                horizontal=True,
                key="post_type_select",
            )

            with st.form("activity_form"):
                if p_type == "help_request":
                    p_title = st.text_input("מה הבקשה? *", placeholder="עזרה בהרכבת ארון, טרמפ לרופא...")
                    p_desc = st.text_area("פירוט הבקשה *", placeholder="ספר/י מה בדיוק נדרש, כמה זמן, האם צריך ציוד...", height=80)
                    pc1, pc2 = st.columns(2)
                    p_date = pc1.date_input("תאריך הבקשה *", min_value=date.today())
                    p_time = pc2.text_input("שעה *", value="12:00", placeholder="12:00")
                    p_location = ""
                    p_seats = 0
                else:
                    p_title = st.text_input("כותרת *", placeholder="ערב פיצה, טרמפ לת\"א...")
                    p_desc = st.text_area("תיאור", placeholder="פרטים נוספים...", height=60)
                    pc1, pc2, pc3 = st.columns(3)
                    p_date = pc1.date_input("תאריך *", min_value=date.today())
                    p_time = pc2.text_input("שעה *", value="18:00", placeholder="18:00")
                    p_seats = pc3.number_input("מקומות פנויים", min_value=1, max_value=100, value=5)
                    p_location = st.text_input("מיקום *", placeholder="חדר מועדון / חניה מרכזית...")

                submit_label = {
                    "activity": "📢 פרסם פעילות",
                    "ride": "📢 פרסם טרמפ",
                    "help_request": "🙏 פרסם בקשת עזרה",
                }[p_type]

                if st.form_submit_button(submit_label, use_container_width=True, type="primary"):
                    # ולידציה לפי סוג — בבקשת עזרה אין שדה 'מיקום' חובה
                    if p_type == "help_request":
                        missing = not p_title or not p_desc or not p_time
                    else:
                        missing = not p_title or not p_location or not p_time

                    if missing:
                        st.error("נא למלא את כל השדות המסומנים ב-*.")
                    else:
                        new_item = {
                            "id": gen_id(), "type": p_type,
                            "title": p_title, "description": p_desc,
                            "event_date": p_date.isoformat(),
                            "event_time": p_time,
                            "location": p_location,
                            "total_seats": p_seats,
                            "organizer_name": cu_post_act["name"], "phone": cu_post_act["phone"],
                            "participants": [],
                            "created_at": datetime.now().isoformat(),
                        }
                        if p_type == "help_request":
                            new_item["volunteers"] = []
                        db.add_activity(new_item)
                        st.success(f"✅ '{p_title}' פורסם!")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  דף ראשי – Home Feed מאוחד מכל המודולים
# ═══════════════════════════════════════════════════════════════════

def _render_feed_card(
    *,
    card_class: str,
    chip_class: str,
    chip_label: str,
    icon: str,
    title: str,
    summary: str,
    meta: str,
    btn_key: str,
    target_page: str,
    focus_key: str | None = None,
    focus_id: str | None = None,
):
    """
    כרטיס פיד עם צבע ייחודי לכל סוג.

    הגישה: מרנדרים את הכרטיס הצבעוני כ-HTML טהור (inline styles — בלי תלות ב-CSS selectors
    שמתנגשים עם Streamlit הפנימי), ואז מוסיפים st.button קטן לניווט מתחתיו.
    כך כל כרטיס מקבל בדיוק את הצבע הנכון ללא תלות בגרסת Streamlit.
    """

    # ── פלטת צבעים לפי סוג כרטיס (לפי תחילית btn_key) ──────────────
    _THEMES = {
        "feed_bulk_":  {
            "bg":         "linear-gradient(135deg,#fff8ec 0%,#ffe8b0 100%)",
            "border":     "#f59e0b",
            "chip_bg":    "#fef3c7",
            "chip_color": "#92400e",
            "title_color":"#78350f",
        },
        "feed_share_": {
            "bg":         "linear-gradient(135deg,#ecfdf5 0%,#a7f3d0 100%)",
            "border":     "#10b981",
            "chip_bg":    "#d1fae5",
            "chip_color": "#065f46",
            "title_color":"#064e3b",
        },
        "feed_gig_":   {
            "bg":         "linear-gradient(135deg,#fdf2f8 0%,#fbcfe8 100%)",
            "border":     "#ec4899",
            "chip_bg":    "#fce7f3",
            "chip_color": "#9d174d",
            "title_color":"#831843",
        },
        "feed_act_":   {
            "bg":         "linear-gradient(135deg,#eff6ff 0%,#bfdbfe 100%)",
            "border":     "#3b82f6",
            "chip_bg":    "#dbeafe",
            "chip_color": "#1e40af",
            "title_color":"#1e3a5f",
        },
        "feed_ride_":  {
            "bg":         "linear-gradient(135deg,#f5f3ff 0%,#ddd6fe 100%)",
            "border":     "#8b5cf6",
            "chip_bg":    "#ede9fe",
            "chip_color": "#5b21b6",
            "title_color":"#4c1d95",
        },
        "feed_help_":  {
            "bg":         "linear-gradient(135deg,#fff7ed 0%,#fed7aa 100%)",
            "border":     "#f97316",
            "chip_bg":    "#ffedd5",
            "chip_color": "#c2410c",
            "title_color":"#7c2d12",
        },
    }

    # בחירת ערכת הצבעים לפי תחילית המפתח
    theme = {
        "bg":         "linear-gradient(135deg,#f8faff 0%,#e0e7ff 100%)",
        "border":     "#6366f1",
        "chip_bg":    "#e0e7ff",
        "chip_color": "#4338ca",
        "title_color":"#1e1b4b",
    }
    for prefix, t in _THEMES.items():
        if btn_key.startswith(prefix):
            theme = t
            break

    # ── רינדור הכרטיס כ-HTML עם inline styles (אין תלות ב-CSS חיצוני) ──
    st.markdown(
        f"""
        <div style="
            background:{theme['bg']};
            border-right:7px solid {theme['border']};
            border-radius:18px 18px 0 0;
            padding:16px 20px 12px 16px;
            margin:8px 0 0 0;
            direction:rtl;
            box-shadow:0 4px 18px rgba(0,0,0,0.08);
            font-family:'Heebo','Rubik','Assistant','Segoe UI',sans-serif;
        ">
            <div style="
                display:inline-block;
                background:{theme['chip_bg']};
                color:{theme['chip_color']};
                font-size:0.72em;
                font-weight:800;
                border-radius:20px;
                padding:3px 10px;
                margin-bottom:10px;
                letter-spacing:0.4px;
            ">{icon} {chip_label}</div>
            <div style="
                font-size:1.05em;
                font-weight:800;
                color:{theme['title_color']};
                margin-bottom:6px;
                line-height:1.35;
            ">{title}</div>
            <div style="
                font-size:0.88em;
                color:#374151;
                margin-bottom:8px;
                line-height:1.5;
            ">{summary}</div>
            <div style="
                font-size:0.78em;
                color:#6b7280;
                line-height:1.4;
            ">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── כפתור ניווט — פותח דף פרטים ייחודי ─────────────────────────
    clicked = st.button("לפרטים ←", key=btn_key, use_container_width=True)

    if clicked:
        # זיהוי סוג הפריט לפי תחילית btn_key
        _TYPE_MAP = {
            "feed_bulk_":  "bulk_deal",
            "feed_share_": "share_item",
            "feed_gig_":   "gig_job",
            "feed_act_":   "activity",
            "feed_ride_":  "ride",
            "feed_help_":  "help_request",
        }
        _itype = "unknown"
        for _pfx, _it in _TYPE_MAP.items():
            if btn_key.startswith(_pfx):
                _itype = _it
                break

        # שמירת הפרטים ב-session_state — main() יזהה ויציג show_item_detail()
        st.session_state["_detail_view"] = {
            "type": _itype,
            "id":   focus_id or btn_key,
        }
        st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  דף פרטים — נפתח בלחיצה על כרטיס בפיד
# ═══════════════════════════════════════════════════════════════════

def _detail_back_btn():
    """כפתור חזרה לפיד — מנקה _detail_view ומרנדר מחדש."""
    if st.button("← חזור לדף הראשי", key="back_from_detail"):
        st.session_state.pop("_detail_view", None)
        st.rerun()
        return True
    return False


def _detail_card_header(icon: str, chip_label: str, title: str,
                         bg: str, border: str, chip_bg: str,
                         chip_color: str, title_color: str):
    """כותרת הכרטיס — אותו סגנון כמו הפיד, רק גדול יותר."""
    st.markdown(
        f"""
        <div style="
            background:{bg};
            border-right:8px solid {border};
            border-radius:18px;
            padding:20px 24px 16px;
            margin-bottom:0;
            direction:rtl;
            font-family:'Heebo','Rubik','Assistant','Segoe UI',sans-serif;
            box-shadow:0 4px 20px rgba(0,0,0,0.08);
        ">
            <div style="
                display:inline-block;
                background:{chip_bg};color:{chip_color};
                font-size:0.8em;font-weight:800;
                border-radius:20px;padding:4px 12px;
                margin-bottom:10px;
            ">{icon} {chip_label}</div>
            <div style="
                font-size:1.45em;font-weight:800;
                color:{title_color};line-height:1.3;
            ">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _detail_row(label: str, value: str):
    """שורת מידע בטבלת הפרטים."""
    st.markdown(
        f"""
        <div style="
            display:flex;justify-content:space-between;
            padding:10px 4px;border-bottom:1px solid #f1f5f9;
            direction:rtl;font-family:'Heebo','Rubik',sans-serif;
        ">
            <span style="color:#6b7280;font-size:0.88em;">{label}</span>
            <span style="font-weight:600;font-size:0.92em;color:#1f2937;">{value}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── פרטי רכישה קבוצתית ─────────────────────────────────────────────
def _show_bulk_detail(deal_id: str, cu: dict | None):
    deal = next((d for d in st.session_state.bulk_deals if d["id"] == deal_id), None)
    if not deal:
        st.warning("העסקה לא נמצאה.")
        return

    emoji = deal.get("product_emoji", "🛒")
    committed = sum(p.get("quantity", 0) for p in deal.get("participants", []))
    status_map = {"open": "🟢 פתוחה", "closed": "🟡 סגורה להזמנה", "done": "✅ הושלמה", "cancelled": "❌ בוטלה"}

    _detail_card_header(
        icon=emoji, chip_label="רכישה קבוצתית", title=deal.get("name", "עסקה"),
        bg="linear-gradient(135deg,#fff8ec,#ffe8b0)",
        border="#f59e0b", chip_bg="#fef3c7", chip_color="#92400e", title_color="#78350f",
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    _detail_row("📦 ספק", deal.get("supplier", "—"))
    _detail_row("📊 סטטוס", status_map.get(deal.get("status", ""), "—"))
    _detail_row("📅 תאריך יעד", deal.get("target_date", "—"))
    _detail_row("👥 משתתפים כרגע", str(len(deal.get("participants", []))))
    _detail_row("📐 גודל ארגז", str(deal.get("box_size", "—")))
    _detail_row("🔢 יחידות שנרשמו", str(committed))
    if deal.get("description"):
        st.markdown(
            f"<div style='background:#fffbf0;border-radius:12px;padding:14px 16px;"
            f"direction:rtl;font-size:0.9em;color:#374151;margin:10px 0;'>"
            f"📝 {deal['description']}</div>",
            unsafe_allow_html=True,
        )
    _detail_row("👤 מארגן", f"{deal.get('organizer_name','—')} · {deal.get('organizer_phone','')}")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # פעולות
    if deal.get("status") == "open":
        if cu:
            already = any(p.get("phone","").strip() == cu["phone"].strip()
                          for p in deal.get("participants", []))
            if already:
                st.success("✅ אתה כבר חלק מהעסקה הזו!")
            else:
                st.markdown("#### 🛒 הצטרפות לעסקה")
                qty = st.number_input("כמות יחידות", min_value=1, max_value=50, value=1, key="detail_bulk_qty")
                if st.button("הצטרף לעסקה!", key="detail_bulk_join", type="primary", use_container_width=True):
                    deal.setdefault("participants", []).append({
                        "name": cu["name"], "phone": cu["phone"], "quantity": qty,
                        "joined_at": datetime.now().isoformat(timespec="seconds"),
                    })
                    db._update_by_id("bulk_deals", deal, id_field="id")
                    db.invalidate_cache()
                    st.success(f"🎉 הצטרפת! הזמנת {qty} יחידות.")
                    st.session_state.bulk_deals = db.get_bulk_deals()
                    st.rerun()
        else:
            st.info("🔒 התחבר/י כדי להצטרף לעסקה.")
    else:
        st.info("העסקה אינה פתוחה כרגע להצטרפות.")


# ── פרטי השאלת ציוד ────────────────────────────────────────────────
def _show_share_detail(item_id: str, cu: dict | None):
    item = next((s for s in st.session_state.share_items if s["id"] == item_id), None)
    if not item:
        st.warning("הפריט לא נמצא.")
        return

    is_offer = item.get("type") == "offer"
    icon = "📦" if is_offer else "🔍"
    chip_label = "מציע להשאיל" if is_offer else "מחפש להשאיל"

    _detail_card_header(
        icon=icon, chip_label=chip_label, title=item.get("item_name", "פריט"),
        bg="linear-gradient(135deg,#ecfdf5,#a7f3d0)",
        border="#10b981", chip_bg="#d1fae5", chip_color="#065f46", title_color="#064e3b",
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    _detail_row("👤 שם", item.get("owner_name", "—"))
    if item.get("condition"):
        _detail_row("⭐ מצב הפריט", item["condition"])
    if item.get("description"):
        st.markdown(
            f"<div style='background:#f0fdf4;border-radius:12px;padding:14px 16px;"
            f"direction:rtl;font-size:0.9em;color:#374151;margin:10px 0;'>"
            f"📝 {item['description']}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # פרטי קשר — מוצגים למשתמש מחובר בלבד
    if cu:
        phone = item.get("phone", "")
        if phone:
            st.markdown(
                f"""<div style="
                    background:#d1fae5;border-radius:14px;padding:16px 20px;
                    direction:rtl;font-family:'Heebo','Rubik',sans-serif;text-align:center;
                ">
                    <div style="font-size:0.8em;color:#065f46;margin-bottom:4px;">📞 לתיאום — התקשר/י ל:</div>
                    <div style="font-size:1.4em;font-weight:800;color:#064e3b;">{phone}</div>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("🔒 התחבר/י כדי לראות פרטי קשר.")


# ── פרטי עבודה מזדמנת ──────────────────────────────────────────────
def _show_gig_detail(job_id: str, cu: dict | None):
    job = next((j for j in st.session_state.gig_jobs if j["id"] == job_id), None)
    if not job:
        st.warning("העבודה לא נמצאה.")
        return

    wage_type = "לשעה" if job.get("wage_type") == "per_hour" else "עבור כל העבודה"

    _detail_card_header(
        icon="💼", chip_label="עבודה מזדמנת", title=job.get("title", "עבודה"),
        bg="linear-gradient(135deg,#fdf2f8,#fbcfe8)",
        border="#ec4899", chip_bg="#fce7f3", chip_color="#9d174d", title_color="#831843",
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    _detail_row("💰 שכר", f"{job.get('wage',0)}₪ {wage_type}")
    _detail_row("📊 סטטוס", {"open":"🟢 פתוח","taken":"🟡 תפוס","done":"✅ הסתיים"}.get(job.get("status",""), "—"))
    _detail_row("👤 מפרסם", job.get("poster_name", "—"))
    if job.get("description"):
        st.markdown(
            f"<div style='background:#fdf2f8;border-radius:12px;padding:14px 16px;"
            f"direction:rtl;font-size:0.9em;color:#374151;margin:10px 0;'>"
            f"📝 {job['description']}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if cu:
        phone = job.get("phone", "")
        if phone:
            st.markdown(
                f"""<div style="
                    background:#fce7f3;border-radius:14px;padding:16px 20px;
                    direction:rtl;font-family:'Heebo','Rubik',sans-serif;text-align:center;
                ">
                    <div style="font-size:0.8em;color:#9d174d;margin-bottom:4px;">📞 פנה/י למפרסם:</div>
                    <div style="font-size:1.4em;font-weight:800;color:#831843;">{phone}</div>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("🔒 התחבר/י כדי לראות פרטי קשר.")


# ── פרטי פעילות / טרמפ / בקשת עזרה ────────────────────────────────
def _show_activity_detail(activity_id: str, cu: dict | None):
    act = next((a for a in st.session_state.activities if a["id"] == activity_id), None)
    if not act:
        st.warning("הפעילות לא נמצאה.")
        return

    a_type = act.get("type", "activity")
    _THEMES_ACT = {
        "activity":     ("🎉", "פעילות",       "linear-gradient(135deg,#eff6ff,#bfdbfe)", "#3b82f6", "#dbeafe", "#1e40af", "#1e3a5f"),
        "ride":         ("🚗", "טרמפ",          "linear-gradient(135deg,#f5f3ff,#ddd6fe)", "#8b5cf6", "#ede9fe", "#5b21b6", "#4c1d95"),
        "help_request": ("🆘", "בקשת עזרה",    "linear-gradient(135deg,#fff7ed,#fed7aa)", "#f97316", "#ffedd5", "#c2410c", "#7c2d12"),
    }
    icon, chip_label, bg, border, chip_bg, chip_color, title_color = _THEMES_ACT.get(a_type, _THEMES_ACT["activity"])

    _detail_card_header(
        icon=icon, chip_label=chip_label, title=act.get("title", "פעילות"),
        bg=bg, border=border, chip_bg=chip_bg, chip_color=chip_color, title_color=title_color,
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    _detail_row("📅 תאריך", act.get("event_date", "—"))
    _detail_row("⏰ שעה",   act.get("event_time", "—"))
    if act.get("location"):
        _detail_row("📍 מיקום", act["location"])
    _detail_row("👤 מארגן", f"{act.get('organizer_name','—')} · {act.get('phone','')}")
    n_participants = len(act.get("participants", []))
    n_volunteers   = len(act.get("volunteers",   []))
    if n_participants:
        _detail_row("🙋 משתתפים", str(n_participants))
    if n_volunteers:
        _detail_row("💪 מתנדבים", str(n_volunteers))
    if act.get("description"):
        st.markdown(
            f"<div style='background:#f8faff;border-radius:12px;padding:14px 16px;"
            f"direction:rtl;font-size:0.9em;color:#374151;margin:10px 0;'>"
            f"📝 {act['description']}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # פעולות לפי סוג
    if cu:
        my_phone = cu["phone"].strip()
        if a_type == "activity":
            already = any(p.get("phone","").strip() == my_phone for p in act.get("participants", []))
            if already:
                st.success("✅ כבר נרשמת לפעילות זו!")
            elif act.get("event_date", "") >= date.today().isoformat():
                if st.button("🙋 אני מגיע/ה!", key="detail_join_act", type="primary", use_container_width=True):
                    act.setdefault("participants", []).append({"name": cu["name"], "phone": my_phone})
                    db._update_by_id("activities", act, id_field="id")
                    db.invalidate_cache()
                    st.success("🎉 נרשמת!")
                    st.session_state.activities = db.get_activities()
                    st.rerun()
        elif a_type == "help_request":
            already_vol = any(v.get("phone","").strip() == my_phone for v in act.get("volunteers", []))
            if already_vol:
                st.success("✅ כבר נרשמת כמתנדב/ת!")
            elif act.get("event_date", "") >= date.today().isoformat():
                if st.button("💪 אני מתנדב/ת!", key="detail_join_help", type="primary", use_container_width=True):
                    act.setdefault("volunteers", []).append({"name": cu["name"], "phone": my_phone})
                    db._update_by_id("activities", act, id_field="id")
                    db.invalidate_cache()
                    st.success("🙏 תודה על ההתנדבות!")
                    st.session_state.activities = db.get_activities()
                    st.rerun()
        elif a_type == "ride":
            already = any(p.get("phone","").strip() == my_phone for p in act.get("participants", []))
            if already:
                st.success("✅ כבר נרשמת לטרמפ!")
            elif act.get("event_date", "") >= date.today().isoformat():
                if st.button("🚗 אני מצטרף/ת לטרמפ!", key="detail_join_ride", type="primary", use_container_width=True):
                    act.setdefault("participants", []).append({"name": cu["name"], "phone": my_phone})
                    db._update_by_id("activities", act, id_field="id")
                    db.invalidate_cache()
                    st.success("👍 הצטרפת!")
                    st.session_state.activities = db.get_activities()
                    st.rerun()
    else:
        st.info("🔒 התחבר/י כדי להשתתף.")


# ── dispatcher ────────────────────────────────────────────────────
def show_item_detail():
    """
    דף פרטים ייחודי לפריט שנבחר — נפתח בלחיצה על כרטיס בפיד.
    מחליף את ההרחבה האינלינית ויוצר דף נקי עם מידע מלא + פעולות.
    """
    detail = st.session_state.get("_detail_view", {})
    item_type = detail.get("type", "")
    item_id   = detail.get("id",   "")

    if not item_id:
        st.session_state.pop("_detail_view", None)
        st.rerun()
        return

    if _detail_back_btn():
        return

    cu = st.session_state.get("current_user")

    if item_type == "bulk_deal":
        _show_bulk_detail(item_id, cu)
    elif item_type == "share_item":
        _show_share_detail(item_id, cu)
    elif item_type == "gig_job":
        _show_gig_detail(item_id, cu)
    elif item_type in ("activity", "ride", "help_request"):
        _show_activity_detail(item_id, cu)
    else:
        st.warning("סוג פריט לא מוכר.")
        st.session_state.pop("_detail_view", None)


def show_home():
    """
    פיד ראשי מאוחד — כיוון B:
      • Hero section עם ברכה אישית + stats מהירים
      • שורת filter chips לסינון לפי סוג
      • כרטיסים צבעוניים (כל סוג בצבעו)
      • Empty state יפה כשאין תוצאות

    סדר: רכישות קבוצתיות תמיד ראשונות,
    שאר הפריטים ממוינים לפי created_at יורד.
    """
    cu = st.session_state.get("current_user")
    greeting_name = cu["name"] if cu else "חבר/ה"

    # ── מצב פילטר (נשמר ב-session_state) ────────────────────────────
    if "feed_filter" not in st.session_state:
        st.session_state["feed_filter"] = "all"
    active_filter = st.session_state["feed_filter"]

    # ── stats לhero ──────────────────────────────────────────────────
    _active_deals_all = [d for d in st.session_state.bulk_deals if d.get("status") == "open"]
    _total_share      = len(st.session_state.share_items)
    _upcoming_acts    = sum(
        1 for a in st.session_state.activities
        if a.get("event_date", "") >= date.today().isoformat()
    )
    _open_jobs = sum(1 for j in st.session_state.gig_jobs if j.get("status") == "open")

    # ── ברכה לפי שעה ─────────────────────────────────────────────────
    _hour = datetime.now().hour
    if _hour < 12:
        _time_greet = "בוקר טוב"
    elif _hour < 17:
        _time_greet = "צהריים טובים"
    elif _hour < 21:
        _time_greet = "ערב טוב"
    else:
        _time_greet = "לילה טוב"

    # ── Hero Section ──────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            background:linear-gradient(135deg,#ecfdf5 0%,#f0fdf4 60%,#dcfce7 100%);
            border-radius:20px;
            padding:20px 24px 18px;
            margin-bottom:10px;
            direction:rtl;
            font-family:'Heebo','Rubik','Assistant','Segoe UI',sans-serif;
            border:1px solid #bbf7d0;
        ">
            <div style="font-size:1.35em;font-weight:800;color:#14532d;margin-bottom:3px;">
                {_time_greet}, {greeting_name}! 🌿
            </div>
            <div style="font-size:0.87em;color:#16a34a;margin-bottom:14px;">
                הנה מה שקורה בכפר עכשיו — לחץ/י על כרטיס לפרטים
            </div>
            <div style="display:flex;gap:9px;flex-wrap:wrap;">
                <div style="background:white;border-radius:12px;padding:7px 13px;border:1px solid #bbf7d0;text-align:center;min-width:54px;">
                    <div style="font-size:1.25em;font-weight:800;color:#f59e0b;">{len(_active_deals_all)}</div>
                    <div style="font-size:0.68em;color:#6b7280;">🛒 קניות</div>
                </div>
                <div style="background:white;border-radius:12px;padding:7px 13px;border:1px solid #bbf7d0;text-align:center;min-width:54px;">
                    <div style="font-size:1.25em;font-weight:800;color:#10b981;">{_total_share}</div>
                    <div style="font-size:0.68em;color:#6b7280;">📦 ציוד</div>
                </div>
                <div style="background:white;border-radius:12px;padding:7px 13px;border:1px solid #bbf7d0;text-align:center;min-width:54px;">
                    <div style="font-size:1.25em;font-weight:800;color:#3b82f6;">{_upcoming_acts}</div>
                    <div style="font-size:0.68em;color:#6b7280;">🎉 פעילויות</div>
                </div>
                <div style="background:white;border-radius:12px;padding:7px 13px;border:1px solid #bbf7d0;text-align:center;min-width:54px;">
                    <div style="font-size:1.25em;font-weight:800;color:#ec4899;">{_open_jobs}</div>
                    <div style="font-size:0.68em;color:#6b7280;">💼 עבודות</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── שורת Filter Chips ─────────────────────────────────────────────
    # 7 סוגי תוכן — הכפתור הפעיל מקבל "✓ " בהתחלה.
    # הכפתורים הם st.button אמיתיים בתוך st.columns, מעוצבים ע"י CSS.
    _filter_opts = [
        ("all",      "הכל"),
        ("bulk",     "🛒 קניות"),
        ("share",    "📦 ציוד"),
        ("gig",      "💼 עבודה"),
        ("activity", "🎉 פעילות"),
        ("ride",     "🚗 טרמפ"),
        ("help",     "🆘 עזרה"),
    ]
    _fcols = st.columns(len(_filter_opts))
    for _fc, (_fk, _fl) in zip(_fcols, _filter_opts):
        _label = f"✓ {_fl}" if _fk == active_filter else _fl
        if _fc.button(_label, key=f"filter_chip_{_fk}", use_container_width=True):
            st.session_state["feed_filter"] = _fk
            st.rerun()

    # ══════════════════════════════════════════
    # חלק 1: רכישות קבוצתיות פעילות (תמיד למעלה)
    # ══════════════════════════════════════════
    active_deals = _active_deals_all
    _show_bulk = (active_filter in ("all", "bulk"))

    if _show_bulk and active_deals:
        st.markdown(
            "<div class='feed-hero-header'>🛒 קבוצות רכישה פעילות עכשיו</div>",
            unsafe_allow_html=True,
        )
        for deal in active_deals:
            # חישוב: כמה יחידות נשארות לארגז הבא
            committed = sum(p.get("quantity", 0) for p in deal.get("participants", []))
            box_size = deal.get("box_size", 1) or 1
            units_in_last_box = committed % box_size
            units_remaining_for_box = (box_size - units_in_last_box) if units_in_last_box else 0
            target_date = deal.get("target_date", "—")
            emoji = deal.get("product_emoji", "🛒")

            if units_remaining_for_box:
                remaining_text = f"עוד {units_remaining_for_box} יחידות לארגז הבא"
            else:
                remaining_text = "ארגז מלא — מחכים להתחלת ארגז חדש"

            summary = f"{deal.get('supplier', '')} · {remaining_text}"
            meta = f"📅 תאריך הזמנה משוער: {target_date} &nbsp; 👥 {len(deal.get('participants', []))} משתתפים"

            _render_feed_card(
                card_class="feed-card-bulk",
                chip_class="chip-bulk",
                chip_label="רכישה קבוצתית",
                icon=emoji,
                title=deal.get("name", "עסקה"),
                summary=summary,
                meta=meta,
                btn_key=f"feed_bulk_{deal['id']}",
                target_page="bulk_buy",
                focus_key="_bulk_focus",
                focus_id=deal["id"],
            )

    # ══════════════════════════════════════════
    # חלק 2: כל השאר — ממוין לפי created_at (חדש → ישן)
    # ══════════════════════════════════════════
    feed_items = []

    # פעילויות / טרמפים / בקשות עזרה
    for a in st.session_state.activities:
        a_type = a.get("type", "activity")
        if a_type == "ride":
            feed_items.append({
                "created_at": a.get("created_at", ""),
                "card_class": "feed-card-ride",
                "chip_class": "chip-ride",
                "chip_label": "טרמפ",
                "icon": "🚗",
                "title": a["title"],
                "summary": a.get("description", "") or "אין פירוט נוסף.",
                "meta": f"📅 {a['event_date']} &nbsp; ⏰ {a['event_time']} &nbsp; 📍 {a.get('location','')} &nbsp; 👤 {a['organizer_name']}",
                "btn_key": f"feed_ride_{a['id']}",
                "target_page": "activities",
                "focus_key": "_activity_focus",
                "focus_id": a["id"],
            })
        elif a_type == "help_request":
            feed_items.append({
                "created_at": a.get("created_at", ""),
                "card_class": "feed-card-help",
                "chip_class": "chip-help",
                "chip_label": "בקשת עזרה",
                "icon": "🆘",
                "title": a["title"],
                "summary": a.get("description", "") or "אין פירוט נוסף.",
                "meta": f"📅 {a['event_date']} &nbsp; ⏰ {a['event_time']} &nbsp; 👤 {a['organizer_name']} &nbsp; 🙋 {len(a.get('volunteers', []))} מתנדבים",
                "btn_key": f"feed_help_{a['id']}",
                "target_page": "activities",
                "focus_key": "_activity_focus",
                "focus_id": a["id"],
            })
        else:  # activity
            feed_items.append({
                "created_at": a.get("created_at", ""),
                "card_class": "feed-card-activity",
                "chip_class": "chip-activity",
                "chip_label": "פעילות",
                "icon": "🎉",
                "title": a["title"],
                "summary": a.get("description", "") or "אין פירוט נוסף.",
                "meta": f"📅 {a['event_date']} &nbsp; ⏰ {a['event_time']} &nbsp; 📍 {a.get('location','')} &nbsp; 👤 {a['organizer_name']}",
                "btn_key": f"feed_act_{a['id']}",
                "target_page": "activities",
                "focus_key": "_activity_focus",
                "focus_id": a["id"],
            })

    # לוח השאלת ציוד
    for s in st.session_state.share_items:
        is_offer = s.get("type") == "offer"
        feed_items.append({
            "created_at": s.get("created_at", ""),
            "card_class": "feed-card-share",
            "chip_class": "chip-share",
            "chip_label": "מציע להשאיל" if is_offer else "מחפש להשאיל",
            "icon": "📦" if is_offer else "🔍",
            "title": s.get("item_name", "פריט"),
            "summary": s.get("description", "") or "אין פירוט נוסף.",
            "meta": f"👤 {s.get('owner_name','')}",
            "btn_key": f"feed_share_{s['id']}",
            "target_page": "share_board",
        })

    # עבודות מזדמנות פתוחות בלבד
    for j in st.session_state.gig_jobs:
        if j.get("status") != "open":
            continue
        wage = j.get("wage", 0)
        wage_type = "לשעה" if j.get("wage_type") == "per_hour" else "עבור כל העבודה"
        feed_items.append({
            "created_at": j.get("created_at", ""),
            "card_class": "feed-card-gig",
            "chip_class": "chip-gig",
            "chip_label": "עבודה מזדמנת",
            "icon": "💼",
            "title": j.get("title", "עבודה"),
            "summary": j.get("description", "") or "אין פירוט נוסף.",
            "meta": f"💰 {wage}₪ {wage_type} &nbsp; 👤 {j.get('poster_name','')}",
            "btn_key": f"feed_gig_{j['id']}",
            "target_page": "gig_jobs",
        })

    # ── פילטור לפי הבחירה ─────────────────────────────────────────────
    # מיפוי: שם פילטר → תחילית btn_key של הפריטים הרלוונטיים
    _PREFIX_MAP = {
        "share":    "feed_share_",
        "gig":      "feed_gig_",
        "activity": "feed_act_",
        "ride":     "feed_ride_",
        "help":     "feed_help_",
    }
    if active_filter == "bulk":
        feed_items = []          # רק רכישות — כבר הוצגו בחלק 1
    elif active_filter in _PREFIX_MAP:
        _pfx = _PREFIX_MAP[active_filter]
        feed_items = [item for item in feed_items if item.get("btn_key", "").startswith(_pfx)]
    # "all" → לא מסננים

    # מיון יורד לפי created_at
    feed_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    # ── הצגת פריטים / Empty State ─────────────────────────────────────
    if feed_items:
        if active_filter == "all":
            st.markdown(
                "<div class='feed-section-header'>📰 מה חדש בכפר</div>",
                unsafe_allow_html=True,
            )
        for item in feed_items:
            item.pop("created_at", None)   # created_at משמש רק למיון
            _render_feed_card(**item)

    elif not active_deals or active_filter not in ("all", "bulk"):
        # ── Empty State יפה ──────────────────────────────────────────
        _EMPTY = {
            "all":      ("🌱", "הכפר שקט עכשיו",          "היה/י הראשון/ה לפרסם משהו!"),
            "bulk":     ("🛒", "אין קניות קבוצתיות פעילות", "פתח/י קבוצת רכישה חדשה"),
            "share":    ("📦", "אין פריטים להשאלה",         "פרסם/י ציוד שיש לך"),
            "gig":      ("💼", "אין עבודות פתוחות",         "פרסם/י עבודה מזדמנת"),
            "activity": ("🎉", "אין פעילויות קרובות",       "הכרז/י על פעילות חדשה"),
            "ride":     ("🚗", "אין טרמפים פעילים",          "פרסם/י טרמפ בלשונית פעילויות"),
            "help":     ("🆘", "אין בקשות עזרה",            "כולם מסתדרים לבד — כרגע 😊"),
        }
        _ei, _et, _es = _EMPTY.get(active_filter, _EMPTY["all"])
        st.markdown(
            f"""
            <div style="
                text-align:center;
                padding:44px 20px;
                direction:rtl;
                font-family:'Heebo','Rubik','Assistant','Segoe UI',sans-serif;
            ">
                <div style="font-size:3.5em;margin-bottom:12px;">{_ei}</div>
                <div style="font-size:1.15em;font-weight:800;color:#374151;margin-bottom:8px;">{_et}</div>
                <div style="font-size:0.88em;color:#9ca3af;">{_es}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════
#  דף נחיתה – כניסה / הרשמה (Firebase Auth)
# ═══════════════════════════════════════════════════════════════════

# ── עזר: מסך 'בדוק את המייל שלך' ──────────────────────────────────
def _show_verify_screen(auth_mod):
    """מסך ביניים — מוצג לאחר הרשמה עד שהמשתמש מאשר את המייל."""
    pending = st.session_state.get("_pending_auth", {})
    email   = pending.get("email", "")
    st.markdown(
        f"""
        <div style="background:#f0f9ff; border-radius:20px; padding:28px;
                    text-align:center; direction:rtl; border:2px solid #0D9488; margin-top:16px;">
            <div style="font-size:3em; margin-bottom:12px;">📧</div>
            <h3 style="color:#0D9488;">בדוק/י את תיבת הדואר!</h3>
            <p style="color:#444;">שלחנו מייל אישור ל-<strong>{email}</strong></p>
            <p style="color:#666; font-size:0.9em;">
                לחץ/י על הקישור במייל ואז חזור/י לכאן להתחבר.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    if c1.button("🔄 שלח מייל שוב", use_container_width=True):
        if auth_mod.resend_verification(pending.get("id_token", "")):
            st.success("נשלח! בדוק/י את תיבת הדואר.")
        else:
            st.error("שגיאה — נסה שוב.")
    if c2.button("← חזור לכניסה", use_container_width=True):
        st.session_state.pop("_auth_state", None)
        st.session_state.pop("_pending_auth", None)
        st.rerun()


# ── עזר: מסך השלמת פרופיל (שם + טלפון) ────────────────────────────
def _show_profile_screen(auth_mod):
    """
    מסך השלמת פרופיל — מוצג לאחר כניסה ראשונה (מייל או Google).
    שם + טלפון נשמרים ב-Google Sheets ומשמשים בכל מודולי האפליקציה.
    """
    pending      = st.session_state.get("_pending_auth", {})
    display_name = pending.get("display_name", "")  # ממולא מראש בכניסה עם Google

    st.markdown(
        """
        <div style="background:#f0fdf4; border-radius:20px; padding:24px;
                    text-align:center; direction:rtl; border:2px solid #0D9488;
                    margin-top:16px; margin-bottom:20px;">
            <div style="font-size:2.5em; margin-bottom:8px;">👋</div>
            <h3 style="color:#0D9488;">כמעט שם! השלם/י את הפרופיל</h3>
            <p style="color:#666;">אנחנו צריכים עוד שני פרטים קטנים</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("profile_completion_form"):
        p_name  = st.text_input("שם מלא *", value=display_name, placeholder="ישראל ישראלי")
        p_phone = st.text_input("מספר טלפון *", placeholder="050-1234567")
        submitted = st.form_submit_button(
            "🏘️ כניסה לכפר!", use_container_width=True, type="primary"
        )
        if submitted:
            if not p_name.strip() or not p_phone.strip():
                st.error("נא למלא שם וטלפון.")
            else:
                # שמירת פרופיל ב-Google Sheets
                auth_mod.save_profile(
                    uid=pending.get("uid", ""),
                    email=pending.get("email", ""),
                    name=p_name.strip(),
                    phone=p_phone.strip(),
                    provider=pending.get("provider", "email"),
                )
                # כניסה לאפליקציה
                auth_mod.set_user(
                    name=p_name.strip(),
                    phone=p_phone.strip(),
                    email=pending.get("email", ""),
                    uid=pending.get("uid", ""),
                    provider=pending.get("provider", "email"),
                )
                st.session_state.pop("_auth_state", None)
                st.session_state.pop("_pending_auth", None)
                st.rerun()


# ── עזר: טפסי כניסה / הרשמה ────────────────────────────────────────
def _show_auth_form(auth_mod):
    """
    טפסי כניסה + הרשמה עם מייל/סיסמה.
    אם Google OAuth מוגדר ב-secrets — מציג גם כפתור 'כניסה עם Google'.
    """
    # ── כניסה עם Google (רק אם client_id ו-client_secret מוגדרים) ──
    if auth_mod.has_google_configured():
        app_url = st.secrets.get("app", {}).get("url", "http://localhost:8501")
        g_url   = auth_mod.google_auth_url(app_url)
        st.markdown(
            f"""
            <div style="margin:16px 0 8px 0; text-align:center;">
                <a href="{g_url}"
                   style="display:inline-flex; align-items:center; gap:10px;
                          background:#fff; border:2px solid #ddd; border-radius:30px;
                          padding:12px 28px; color:#444; font-weight:600;
                          text-decoration:none; font-size:1em;
                          box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                         width="22" height="22" style="flex-shrink:0;" />
                    כניסה עם Google
                </a>
            </div>
            <div style="text-align:center; color:#aaa; margin:12px 0; font-size:0.95em;">
                ─── או ───
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── טאבים: כניסה / הרשמה ──
    tab_login, tab_register = st.tabs(["🔑 כניסה", "✨ הרשמה"])

    # ════ כניסה ════
    with tab_login:
        with st.form("login_form"):
            email    = st.text_input("מייל", placeholder="you@example.com", key="li_email")
            password = st.text_input("סיסמה", type="password", placeholder="••••••", key="li_pass")
            submitted = st.form_submit_button(
                "כניסה לכפר 🏘️", use_container_width=True, type="primary"
            )
            if submitted:
                if not email or not password:
                    st.error("נא למלא מייל וסיסמה.")
                else:
                    res = auth_mod.sign_in(email.strip(), password)
                    if res["ok"]:
                        # בדיקה: האם קיים פרופיל ב-Sheets?
                        profile = auth_mod.load_profile(res["email"])
                        if profile and profile.get("phone") and profile.get("name"):
                            auth_mod.set_user(
                                profile["name"], profile["phone"],
                                res["email"], res.get("uid", ""), res.get("provider", "email"),
                            )
                            st.rerun()
                        else:
                            # כניסה ראשונה — צריך להשלים פרופיל
                            st.session_state["_auth_state"]  = "complete_profile"
                            st.session_state["_pending_auth"] = res
                            st.rerun()
                    elif res.get("error") == "verify_needed":
                        # מייל לא אומת — מעבר למסך אישור
                        st.session_state["_auth_state"]  = "verify_email"
                        st.session_state["_pending_auth"] = {
                            "email":    email.strip(),
                            "id_token": res.get("id_token", ""),
                        }
                        st.rerun()
                    else:
                        st.error(res["error"])

        # שכחת סיסמה
        with st.expander("🔓 שכחת סיסמה?"):
            reset_email = st.text_input("מייל לאיפוס", key="reset_email_field",
                                        placeholder="you@example.com")
            if st.button("שלח מייל איפוס", key="reset_send_btn", use_container_width=True):
                if reset_email.strip():
                    if auth_mod.send_password_reset(reset_email.strip()):
                        st.success("נשלח! בדוק/י את תיבת הדואר.")
                    else:
                        st.error("שגיאה — בדוק/י שהמייל רשום במערכת.")
                else:
                    st.warning("הכנס/י כתובת מייל.")

    # ════ הרשמה ════
    with tab_register:
        with st.form("register_form"):
            r_email = st.text_input("מייל *", placeholder="you@example.com", key="reg_email")
            r_pass  = st.text_input(
                "סיסמה * (לפחות 6 תווים)", type="password",
                placeholder="••••••", key="reg_pass",
            )
            r_pass2 = st.text_input(
                "אישור סיסמה *", type="password",
                placeholder="••••••", key="reg_pass2",
            )
            submitted = st.form_submit_button(
                "הרשמה ✨", use_container_width=True, type="primary"
            )
            if submitted:
                if not r_email or not r_pass or not r_pass2:
                    st.error("נא למלא את כל השדות.")
                elif r_pass != r_pass2:
                    st.error("הסיסמאות לא תואמות.")
                elif len(r_pass) < 6:
                    st.error("הסיסמה חייבת להכיל לפחות 6 תווים.")
                else:
                    res = auth_mod.sign_up(r_email.strip(), r_pass)
                    if res["ok"]:
                        # הרשמה הצליחה — מעבר למסך אישור מייל
                        st.session_state["_auth_state"]  = "verify_email"
                        st.session_state["_pending_auth"] = {
                            "email":    r_email.strip(),
                            "id_token": res["id_token"],
                        }
                        st.rerun()
                    else:
                        st.error(res["error"])


# ── מסך הנחיתה הראשי ────────────────────────────────────────────────
def show_landing():
    """
    מסך כניסה/הרשמה — מטפל בכל שלבי ה-auth.
    מצבים (via _auth_state):
      None               → טפסי כניסה/הרשמה
      "verify_email"     → 'בדוק/י את תיבת הדואר'
      "complete_profile" → השלמת שם + טלפון
    """
    import auth as auth_mod

    # ── Hero (אותו עיצוב קיים) ──
    st.markdown(
        """
        <div class="landing-hero">
            <h1>שלום חבר/ה הכפר! 🏘️</h1>
            <div class="landing-emojis">🐱 🌊 🌴 🚐 🛺</div>
            <p class="landing-tagline">
                ברוכים הבאים ל-<strong>Kfar-Link</strong> — הפלטפורמה הקהילתית של הכפר.
            </p>
            <p class="landing-sub">
                קבוצות רכישה · טרמפים · השאלת ציוד · עבודות מזדמנות · עזרה הדדית
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Auth ──
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        auth_state = st.session_state.get("_auth_state")
        if auth_state == "verify_email":
            _show_verify_screen(auth_mod)
        elif auth_state == "complete_profile":
            _show_profile_screen(auth_mod)
        else:
            _show_auth_form(auth_mod)


# ═══════════════════════════════════════════════════════════════════
#  מסך ראשי – ניהול ניווט
# ═══════════════════════════════════════════════════════════════════

def main():
    init_state()

    import auth as auth_mod

    # ── Google OAuth callback ──────────────────────────────────────
    # כאשר Google מפנה חזרה לאפליקציה לאחר אימות, הוא מוסיף ?code=...&state=kfar_google
    # אנחנו קוראים את הפרמטרים, מחליפים ב-Firebase token ומגדירים את המשתמש.
    qp_early = st.query_params
    if qp_early.get("state") == "kfar_google" and "code" in qp_early:
        code         = qp_early["code"]
        redirect_uri = st.secrets.get("app", {}).get("url", "http://localhost:8501")
        st.query_params.clear()
        result = auth_mod.handle_google_code(code, redirect_uri)
        if result["ok"]:
            profile = auth_mod.load_profile(result["email"])
            if profile and profile.get("phone") and profile.get("name"):
                # פרופיל קיים — כניסה ישירה
                auth_mod.set_user(
                    profile["name"], profile["phone"],
                    result["email"], result.get("uid", ""), "google",
                )
            else:
                # כניסה ראשונה — השלמת פרופיל
                st.session_state["_auth_state"]  = "complete_profile"
                st.session_state["_pending_auth"] = result
        else:
            st.error(result.get("error", "שגיאה בכניסה עם Google."))
        st.rerun()

    # ── טיפול ב-query params מקליקים על כרטיסי הפיד ──
    # דוגמה: ?nav=bulk_buy&focus_id=demo1&focus_key=_bulk_focus
    # אנחנו מעבירים את הערכים ל-session_state ואז מנקים את ה-URL.
    qp = st.query_params
    if "nav" in qp:
        st.session_state["_nav_override"] = qp["nav"]
        fid = qp.get("focus_id")
        fkey = qp.get("focus_key")
        if fid and fkey:
            st.session_state[fkey] = fid
        elif fid:
            # ברירת מחדל — אם אין focus_key, משתמשים ב-_activity_focus
            st.session_state["_activity_focus"] = fid
        st.query_params.clear()
        st.rerun()

    # ── אם המשתמש לא מחובר – דף נחיתה מלא (ללא sidebar) ──
    cu = st.session_state.get("current_user")
    if not cu:
        show_landing()
        return

    # ── Sidebar (מוצג רק למשתמש מחובר) ──────────────────────────
    with st.sidebar:
        st.markdown("## 🏄‍♂️ Kfar-Link")
        st.caption("כפר סטודנטים מחובר 🐱")
        st.divider()

        st.success(f"👤 מחובר/ת כ: **{cu['name']}**")
        st.caption(f"📞 {cu['phone']}")
        if st.button("🚪 התנתק", use_container_width=True, key="logout_btn"):
            auth_mod.logout()   # מנקה current_user + כל מצב auth
            st.rerun()

        st.divider()

        # ── ניווט — כפתורים עצמאיים (במקום st.radio) ──
        # מדוע: המשתמש ציין שהתווית "ניווט" הופיעה ככפתור שאינו עושה כלום,
        # ושה-radio buttons לא היו מזמינים ללחיצה. החלפנו לכפתורים אמיתיים:
        # כל דף הוא st.button מלא-רוחב, עם מצב active המובלט בצבע.
        nav_options = ["home", "bulk_buy", "share_board", "gig_jobs", "activities"]
        nav_labels = {
            "home": "🏠 דף ראשי",
            "bulk_buy": "🛒 קבוצת רכישה",
            "share_board": "🔧 השאלת ציוד",
            "gig_jobs": "💼 עבודות מזדמנות",
            "activities": "🗓️ פעילויות ועזרה הדדית",
        }

        # ניהול המצב: תומך גם במעבר מהפיד ומאזור 'הפעילויות שלי'
        nav_override = st.session_state.pop("_nav_override", None)
        if nav_override in nav_options:
            st.session_state["nav_radio"] = nav_override
        elif "nav_radio" not in st.session_state:
            st.session_state["nav_radio"] = "home"

        # כותרת הניווט (טקסט בלבד — לא כפתור)
        st.markdown(
            "<div class='sidebar-nav-header'>🧭 ניווט</div>",
            unsafe_allow_html=True,
        )

        # רינדור הכפתורים אחד אחרי השני. הכפתור הפעיל מקבל key עם סיומת _active
        # כדי שה-CSS יוכל לטרגט אותו דרך `[class*="st-key-nav_btn_"][class*="_active"]`.
        # ב-Streamlit 1.36+ ה-key הופך ל-class בשם st-key-{key} על element container.
        current_page = st.session_state.get("nav_radio", "home")
        for nav_key in nav_options:
            is_active = current_page == nav_key
            btn_key = f"nav_btn_{nav_key}_active" if is_active else f"nav_btn_{nav_key}"
            if st.button(
                nav_labels[nav_key],
                key=btn_key,
                use_container_width=True,
            ):
                # לחיצה = מעבר לעמוד. נקבע בסייר הסשן ונרנדר מחדש.
                st.session_state["nav_radio"] = nav_key
                st.rerun()

        page = st.session_state.get("nav_radio", "home")

        st.divider()

        # ── סיכום מהיר ──
        st.markdown("### 📊 סיכום")
        open_deals = sum(1 for d in st.session_state.bulk_deals if d["status"] == "open")
        open_jobs = sum(1 for j in st.session_state.gig_jobs if j["status"] == "open")
        upcoming = sum(
            1 for a in st.session_state.activities
            if a["event_date"] >= date.today().isoformat()
        )
        st.metric("עסקאות פעילות", open_deals)
        st.metric("משרות פתוחות", open_jobs)
        st.metric("פעילויות קרובות", upcoming)
        st.metric("פריטים להשאלה", len(st.session_state.share_items))

        # ── הפעילויות שלי ─────────────────────────────────────
        # מציג למשתמש המחובר את כל הפריטים שהוא מעורב בהם,
        # עם כפתור 'מעבר מהיר' וחישוב סכום לתשלום בעסקאות סגורות.
        if cu:
            st.divider()
            st.markdown("### 📌 הפעילויות שלי")
            my_phone = cu["phone"].strip()
            has_items = False
            _jump_counter = 0  # מונה ייחודי לכפתורי מעבר מהיר

            # ── עסקאות רכישה ──
            my_deals_organizer = [
                d for d in st.session_state.bulk_deals
                if d.get("organizer_phone", "").strip() == my_phone
            ]
            my_deals_participant = [
                d for d in st.session_state.bulk_deals
                if d.get("organizer_phone", "").strip() != my_phone
                and any(p.get("phone", "").strip() == my_phone for p in d.get("participants", []))
            ]
            if my_deals_organizer or my_deals_participant:
                has_items = True
                st.markdown("**🛒 עסקאות רכישה:**")
                for d in my_deals_organizer:
                    st.caption(f"  👑 מארגן: {d['name']}")
                    _jump_counter += 1
                    if st.button("🔎 מעבר מהיר", key=f"jump_deal_{_jump_counter}", use_container_width=True):
                        st.session_state["_nav_override"] = "bulk_buy"
                        st.rerun()
                for d in my_deals_participant:
                    p_info = next((p for p in d["participants"] if p.get("phone","").strip() == my_phone), None)
                    qty = p_info["quantity"] if p_info else 0
                    qty_str = f" ({qty} יח')" if p_info else ""
                    # חישוב סכום לתשלום בעסקאות סגורות
                    d_pricing = calculate_bulk_price(d)
                    d_status  = get_deal_status(d, d_pricing)
                    if d_status["code"] == "closed" and qty > 0:
                        pay_amount = round(d_pricing.get("target_price", 0) * qty, 2)
                        st.caption(f"  🙋 משתתף: {d['name']}{qty_str}")
                        st.caption(f"  💳 **לתשלום: {pay_amount}₪**")
                    else:
                        st.caption(f"  🙋 משתתף: {d['name']}{qty_str}")
                    _jump_counter += 1
                    if st.button("🔎 מעבר מהיר", key=f"jump_deal_{_jump_counter}", use_container_width=True):
                        st.session_state["_nav_override"] = "bulk_buy"
                        st.rerun()

            # ── עבודות ──
            my_jobs = [
                j for j in st.session_state.gig_jobs
                if j.get("phone", "").strip() == my_phone
            ]
            if my_jobs:
                has_items = True
                st.markdown("**💼 עבודות שפרסמתי:**")
                for j in my_jobs:
                    status_icon = {"open": "🟢", "taken": "🟡", "done": "⚫"}.get(j["status"], "")
                    st.caption(f"  {status_icon} {j['title']}")
                    _jump_counter += 1
                    if st.button("🔎 מעבר מהיר", key=f"jump_job_{_jump_counter}", use_container_width=True):
                        st.session_state["_nav_override"] = "gig_jobs"
                        st.rerun()

            # ── פעילויות וטרמפים ──
            my_acts_organizer = [
                a for a in st.session_state.activities
                if a.get("phone", "").strip() == my_phone
            ]
            my_acts_participant = [
                a for a in st.session_state.activities
                if a.get("phone", "").strip() != my_phone
                and any(p.get("phone", "").strip() == my_phone for p in a.get("participants", []))
            ]
            if my_acts_organizer or my_acts_participant:
                has_items = True
                st.markdown("**🗓️ פעילויות ועזרה הדדית:**")
                for a in my_acts_organizer:
                    type_icon = "🚗" if a["type"] == "ride" else "🎉"
                    st.caption(f"  👑 מארגן: {type_icon} {a['title']} ({a['event_date']})")
                    _jump_counter += 1
                    if st.button("🔎 מעבר מהיר", key=f"jump_act_{_jump_counter}", use_container_width=True):
                        st.session_state["_nav_override"] = "activities"
                        st.rerun()
                for a in my_acts_participant:
                    type_icon = "🚗" if a["type"] == "ride" else "🎉"
                    st.caption(f"  🙋 משתתף: {type_icon} {a['title']} ({a['event_date']})")
                    _jump_counter += 1
                    if st.button("🔎 מעבר מהיר", key=f"jump_act_{_jump_counter}", use_container_width=True):
                        st.session_state["_nav_override"] = "activities"
                        st.rerun()

            # ── השאלת ציוד ──
            my_shares = [
                s for s in st.session_state.share_items
                if s.get("phone", "").strip() == my_phone
            ]
            if my_shares:
                has_items = True
                st.markdown("**🔧 פריטים שפרסמתי:**")
                for s in my_shares:
                    s_icon = "📦" if s["type"] == "offer" else "🔍"
                    st.caption(f"  {s_icon} {s['item_name']}")
                    _jump_counter += 1
                    if st.button("🔎 מעבר מהיר", key=f"jump_share_{_jump_counter}", use_container_width=True):
                        st.session_state["_nav_override"] = "share_board"
                        st.rerun()

            if not has_items:
                st.caption("אין לך פעילויות עדיין. הצטרף למשהו!")

        st.divider()
        st.caption("MVP · Kfar-Link © 2025\nBuilt with ❤️ + Streamlit")

        # ── כפתור סגירת ה-sidebar ───────────────────────────────
        # onclick: מחפש את כפתור הקפל של Streamlit ולוחץ עליו.
        _sq = "'"   # גרש בודד — כדי להימנע מ-escape מסובך
        _close_js = (
            "const s=["
            + _sq + "[data-testid=stSidebarCollapseButton] button" + _sq + ","
            + _sq + "button[aria-label=Collapse sidebar]" + _sq
            + "];for(const q of s){const b=document.querySelector(q);if(b){b.click();break;}}"
        )
        _close_style = (
            "width:100%;border:1px solid rgba(0,0,0,0.12);border-radius:14px;"
            "padding:11px 16px;background:rgba(255,255,255,0.55);cursor:pointer;"
            "font-size:13px;font-weight:700;color:#374151;direction:rtl;"
            "font-family:Heebo,Rubik,sans-serif;margin-top:4px;"
        )
        _btn_html = (
            '<button onclick="' + _close_js + '" style="' + _close_style + '">'
            + "← סגור תפריט</button>"
        )
        st.markdown(_btn_html, unsafe_allow_html=True)

    # ── ניתוב לדף הנכון ──────────────────────────────
    # אם יש _detail_view — דף פרטים ייחודי ללא קשר לניווט הנוכחי
    if st.session_state.get("_detail_view"):
        show_item_detail()
    elif page == "home":
        show_home()
    elif page == "bulk_buy":
        show_bulk_buy()
    elif page == "share_board":
        show_share_board()
    elif page == "gig_jobs":
        show_gig_jobs()
    elif page == "activities":
        show_activities()


if __name__ == "__main__" or True:
    main()


#בשביל להריץ לוקאלי: streamlit run app.py#
