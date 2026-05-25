# Page Override: Dashboard

> Overrides `MASTER.md` ONLY for the dashboard page.
> Anything not specified here inherits from Master.

**Page:** dashboard.html
**Generated:** 2026-05-03
**Mood:** קהילה חיה, תחושת קמפינג וים, פעילות אמיתית

---

## Hero

- **Style:** Personal welcome ("שלום, [שם]")
- **Background:** Gradient `var(--primary-deep) → var(--primary) → var(--orange)` (135deg)
- **Decoration:** Soft radial glow (white 8% opacity) בפינה
- **Stats:** 3 מטריקות חיות (חברים פעילים, פוסטים היום, עסקאות פתוחות)
- **Stat unit color:** `#FED7AA` (peach — בולט על הרקע הטיל-כתום)

## Activity Feed

הסקציה הכי חשובה בדאשבורד — חייבת להרגיש "חיה".

- **Activity item layout:** אייקון מימין (40×40, radius-12) + תוכן + זמן
- **Icon backgrounds (cycle):**
  - `var(--leaf)` + `var(--primary)` — פעילות קהילתית (טיל)
  - `var(--orange-soft)` + `var(--orange-deep)` — עסקאות / batch buying
  - `var(--primary-soft)` + `var(--primary-deep)` — השאלות / share
- **Animation:** עדכוני live עם fade-in 300ms

## Cards

- **Type:** Bento grid — כרטיסי "מצב נוכחי" בגדלים שונים
- **Hierarchy:** הכרטיס הראשון (active community) הכי גדול
- **Hover:** translateY(-3px) + shadow-md
- **Border:** `1px solid var(--border)` תמיד

## CTA Placement

בדאשבורד אין CTA "הצטרפו" (המשתמש כבר בפנים). במקום זה:
- "פתחו עסקה חדשה" — `var(--orange)` button
- "הזמינו חבר" — `var(--primary)` button (secondary)

## What's Different from Master

| Aspect | Master | Dashboard Override |
|--------|--------|--------------------|
| Hero gradient | Teal-only | Teal → Orange (3-stop) |
| Section count | 4 (Hero, Topics, Members, CTA) | Bento grid (no fixed sections) |
| Primary action | "Join" | "Open new deal" / "Invite friend" |
| Pulse indicator | על member count | על activity dot של כל פעילות חיה |

## Anti-Patterns Specific to Dashboard

- Don't use Fira Code/Mono — שובר את הוויב הקהילתי-חם
- Don't make it look "data-heavy" — זה קהילה, לא analytics
- Don't auto-refresh aggressively — annoying. רק על action.
