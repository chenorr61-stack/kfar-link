"""
auth.py — מודול אימות משתמשים לכפר-לינק
==========================================
תומך ב:
  1. מייל + סיסמה (pyrebase4 + Firebase Auth)
  2. כניסה עם Google (OAuth 2.0 → Firebase REST API)

תהליך הרשמה:
  הרשמה → Firebase שולח מייל אישור → משתמש מאשר →
  כניסה → השלמת פרופיל (שם + טלפון) → כניסה לאפליקציה

תהליך כניסה חוזרת:
  מייל/Google → בדיקת פרופיל קיים ב-Google Sheets → כניסה ישירה
"""
from __future__ import annotations

import urllib.parse
from datetime import datetime

import requests
import pyrebase
import streamlit as st

import db  # שכבת הגישה ל-Google Sheets


# ─────────────────────────────────────────────────
#  אתחול Firebase
# ─────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _firebase_auth():
    """
    מחזיר אובייקט Firebase Auth — cached לכל ה-session.
    pyrebase4 מטפל בתקשורת מול Firebase REST API.
    """
    cfg = {
        "apiKey":            st.secrets["firebase"]["api_key"],
        "authDomain":        st.secrets["firebase"]["auth_domain"],
        "projectId":         st.secrets["firebase"]["project_id"],
        "storageBucket":     st.secrets["firebase"]["storage_bucket"],
        "messagingSenderId": st.secrets["firebase"]["messaging_sender_id"],
        "appId":             st.secrets["firebase"]["app_id"],
        "databaseURL": "",   # לא בשימוש — Google Sheets הוא מסד הנתונים
    }
    return pyrebase.initialize_app(cfg).auth()


# ─────────────────────────────────────────────────
#  מייל + סיסמה
# ─────────────────────────────────────────────────

def sign_up(email: str, password: str) -> dict:
    """
    יוצר חשבון חדש ב-Firebase ושולח מייל אישור אוטומטית.
    מחזיר {"ok": True, uid, id_token, email} או {"ok": False, "error": str}.

    הלוגיקה:
      Firebase יוצר את המשתמש → שולח מייל עם קישור אישור →
      המשתמש לא יוכל להיכנס עד שיאשר את המייל.
    """
    try:
        fa   = _firebase_auth()
        user = fa.create_user_with_email_and_password(email, password)
        fa.send_email_verification(user["idToken"])  # שליחת מייל אישור
        return {
            "ok":       True,
            "uid":      user["localId"],
            "id_token": user["idToken"],
            "email":    email,
        }
    except Exception as e:
        msg = str(e)
        if "EMAIL_EXISTS" in msg:
            return {"ok": False, "error": "המייל הזה כבר רשום. נסה להתחבר."}
        if "WEAK_PASSWORD" in msg:
            return {"ok": False, "error": "הסיסמה חלשה מדי — לפחות 6 תווים."}
        if "INVALID_EMAIL" in msg:
            return {"ok": False, "error": "כתובת מייל לא תקינה."}
        return {"ok": False, "error": "שגיאה בהרשמה. נסה שוב."}


def sign_in(email: str, password: str) -> dict:
    """
    כניסה עם מייל + סיסמה.
    בודק שהמייל אומת לפני הכניסה — מניעת גישה ללא אישור.
    מחזיר {"ok": True, ...} | {"ok": False, "error": "verify_needed"|str}.
    """
    try:
        fa   = _firebase_auth()
        user = fa.sign_in_with_email_and_password(email, password)

        # בדיקת אימות מייל — Firebase שומר את הסטטוס בחשבון
        info     = fa.get_account_info(user["idToken"])
        verified = info["users"][0].get("emailVerified", False)

        if not verified:
            # מייל לא אומת — מחזירים סטטוס מיוחד כדי להציג מסך "בדוק מייל"
            return {
                "ok":       False,
                "error":    "verify_needed",
                "id_token": user["idToken"],
                "email":    email,
            }
        return {
            "ok":       True,
            "uid":      user["localId"],
            "email":    email,
            "id_token": user["idToken"],
            "provider": "email",
        }
    except Exception as e:
        msg = str(e)
        if any(x in msg for x in ("INVALID_LOGIN_CREDENTIALS", "INVALID_PASSWORD", "EMAIL_NOT_FOUND")):
            return {"ok": False, "error": "מייל או סיסמה שגויים."}
        return {"ok": False, "error": "שגיאה בכניסה. נסה שוב."}


def resend_verification(id_token: str) -> bool:
    """שולח מחדש מייל אישור — למשתמש שלא קיבל / מחק את המייל."""
    try:
        _firebase_auth().send_email_verification(id_token)
        return True
    except Exception:
        return False


def send_password_reset(email: str) -> bool:
    """שולח מייל איפוס סיסמה. Firebase מטפל בכל הלוגיקה."""
    try:
        _firebase_auth().send_password_reset_email(email)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────
#  Google OAuth (REST API)
# ─────────────────────────────────────────────────

_GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_FIREBASE_IDP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp"


def google_auth_url(redirect_uri: str) -> str:
    """
    מייצר URL לכניסה עם Google.
    redirect_uri = כתובת האפליקציה (Streamlit מקבל את ה-code דרך query params).
    """
    params = {
        "client_id":     st.secrets["google"]["client_id"],
        "redirect_uri":  redirect_uri,
        "scope":         "email profile openid",
        "response_type": "code",
        "state":         "kfar_google",   # מזהה ייחודי לזיהוי callback
        "prompt":        "select_account",
    }
    return f"{_GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def handle_google_code(code: str, redirect_uri: str) -> dict:
    """
    מחליף authorization code ב-Firebase user (תהליך OAuth 2-שלבי):
      שלב 1: code → Google tokens (access_token + id_token)
      שלב 2: Google id_token → Firebase token + פרטי משתמש

    מחזיר dict עם פרטי המשתמש, או {"ok": False, "error": str}.
    """
    api_key = st.secrets["firebase"]["api_key"]

    # שלב 1: החלפת code ב-Google tokens
    tok_resp = requests.post(_GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     st.secrets["google"]["client_id"],
        "client_secret": st.secrets["google"]["client_secret"],
        "redirect_uri":  redirect_uri,
        "grant_type":    "authorization_code",
    }, timeout=10)
    tokens          = tok_resp.json()
    id_token_google = tokens.get("id_token")
    if not id_token_google:
        return {"ok": False, "error": "שגיאה בכניסה עם Google. נסה שוב."}

    # שלב 2: Google ID token → Firebase user
    fb_resp = requests.post(
        f"{_FIREBASE_IDP_URL}?key={api_key}",
        json={
            "requestUri":          redirect_uri,
            "postBody":            f"id_token={id_token_google}&providerId=google.com",
            "returnSecureToken":   True,
            "returnIdpCredential": True,
        },
        timeout=10,
    )
    data = fb_resp.json()
    if "error" in data:
        return {"ok": False, "error": "כניסה עם Google נכשלה. נסה שוב."}

    return {
        "ok":          True,
        "uid":         data.get("localId"),
        "email":       data.get("email"),
        "display_name": data.get("displayName", ""),
        "id_token":    data.get("idToken"),
        "provider":    "google",
    }


def has_google_configured() -> bool:
    """בודק האם Google OAuth מוגדר ב-secrets (client_id + client_secret)."""
    g = st.secrets.get("google", {})
    return bool(g.get("client_id") and g.get("client_secret"))


# ─────────────────────────────────────────────────
#  פרופיל משתמש (Google Sheets)
# ─────────────────────────────────────────────────

def load_profile(email: str) -> dict | None:
    """
    מחפש פרופיל ב-Google Sheets לפי מייל.
    מחזיר None אם לא קיים (כניסה ראשונה — יש להשלים פרופיל).
    """
    users = db.get_users()
    return next(
        (u for u in users if str(u.get("email", "")).strip().lower() == email.strip().lower()),
        None,
    )


def save_profile(uid: str, email: str, name: str, phone: str, provider: str = "email"):
    """
    שומר/מעדכן פרופיל ב-Google Sheets.
    אם קיים לפי מייל — מעדכן; אחרת — מוסיף שורה חדשה.

    הערה: הגיליון צריך לכלול עמודות: phone, name, email, firebase_uid, provider, first_seen, last_seen
    """
    now      = datetime.now().isoformat(timespec="seconds")
    existing = load_profile(email)

    if existing and existing.get("phone"):
        # עדכון פרופיל קיים
        existing.update({"name": name, "phone": phone, "last_seen": now})
        db._update_by_id("users", existing, id_field="phone")
    else:
        # יצירת פרופיל חדש
        db._append_row("users", {
            "phone":        phone,
            "name":         name,
            "email":        email,
            "firebase_uid": uid,
            "provider":     provider,
            "first_seen":   now,
            "last_seen":    now,
        })
    db.invalidate_cache()


# ─────────────────────────────────────────────────
#  Session State
# ─────────────────────────────────────────────────

def set_user(name: str, phone: str, email: str, uid: str = "", provider: str = "email"):
    """
    מגדיר את המשתמש הנוכחי ב-session_state.
    current_user משמש בכל הפעולות (הצטרפות, פרסום וכו').
    """
    st.session_state.current_user = {
        "name":     name,
        "phone":    phone,
        "email":    email,
        "uid":      uid,
        "provider": provider,
    }


def logout():
    """מנקה את כל מצב ה-auth ומחזיר לדף הכניסה."""
    for key in ["current_user", "_auth_state", "_pending_auth", "_auth_resend_ok"]:
        st.session_state.pop(key, None)
