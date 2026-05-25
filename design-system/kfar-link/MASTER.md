# Design System Master File — Kfar-Link

> **LOGIC:** When building a specific page, first check `design-system/kfar-link/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Kfar-Link — Community ERP for student village
**Generated:** 2026-05-03 (via ui-ux-pro-max skill)
**Category:** Community / Forum / Marketplace (P2P)
**Vision:** ים, עצים, קרוואנים, חברים, חיוכים, חתולים — צבעוני, חמים, קהילתי

---

## Global Rules

### Color Palette — Beach Camping

מבוסס על "Veterinary Clinic — Caring Teal + Warm Orange" מהמאגר. שילוב מאוזן של ים-עצים (טיל) ושקיעת קרוואן (כתום).

| Role | Hex | CSS Variable | שימוש |
|------|-----|--------------|--------|
| Primary | `#0D9488` | `--primary` | טיל-ים — מותג, headers, primary buttons |
| Primary Deep | `#0F766E` | `--primary-deep` | טיל עמוק — hover על primary |
| Primary Soft | `#CCFBF1` | `--primary-soft` | רקע soft, badges |
| Active/Online | `#14B8A6` | `--green` | אינדיקטור "פעיל" — pulse, online dot |
| CTA / Accent | `#F97316` | `--orange` | כתום שקיעה — CTA ראשי, "הצטרפו" |
| CTA Hover | `#C2410C` | `--orange-deep` | כתום עמוק — hover על CTA |
| Background Soft | `#F0FDFA` | `--leaf` | מנטה רכה — קרדיטים, באדג'ים |
| Background | `#FAFEFC` | `--bg` | רקע ראשי |
| Sand | `#FFFBF0` | `--sand` | סקציות אלטרנטיביות |
| Text | `#134E4A` | `--ink` | טיל עמוק לטקסט |
| Border | `#D1F5EE` | `--border` | גבול עדין במנטה |

**Color Strategy:** Warm, welcoming. תמונות חברים מוסיפות אנושיות. Topic badges בצבעי טיל. אינדיקטורי פעילות במנטה-טיל. CTA כתום שקיעה לבולטות.

### Typography

- **All text:** Heebo (300–800)
- **Mood:** עברית מצוינת, נקי, מקצועי, עם נשמה
- **CSS:** `font-family: 'Heebo', 'Inter', -apple-system, sans-serif;`
- **Font weights in use:** 300 (light), 400 (regular), 500 (medium), 600 (semibold), 700 (bold), 800 (extrabold)

### Pattern: Community/Forum Landing

**Section order:**
1. Hero (community value prop) — gradient teal→orange ברקע
2. Popular topics/categories — קרדיטים מנטה
3. Active members showcase — פוטו של חברים פעילים
4. Join CTA — כתום בולט

**CTA placement:** Join button prominent + after member showcase
**Conversion focus:** Show active community (member count, posts today). Highlight benefits. Easy onboarding.

### Style: Vibrant & Block-based

- Bold, energetic, playful
- Block layout, geometric shapes
- High color contrast (טיל × כתום)
- Performance: ⚡ Good
- Best for: youth-focused, community, consumer

### Key Effects

- Large sections (48px+ gaps) — `--space-7` ומעלה
- Animated patterns — pulse על "active" indicators
- Bold hover (color shift, not scale)
- Smooth transitions 200-300ms
- Large type (32px+ for hero)

### Anti-Patterns to Avoid

- Generic design (no brand identity)
- Hidden services (everything must be discoverable)
- Heavy skeuomorphism
- Accessibility ignored
- Emoji as icons (use SVG: Heroicons / Lucide / inline SVG)

---

## Pre-Delivery Checklist

### Visual Quality
- [ ] No emojis used as UI icons (use SVG)
- [ ] All icons from consistent icon set
- [ ] Hover states don't cause layout shift
- [ ] Use CSS variables (`var(--primary)`) not hex literals

### Interaction
- [ ] All clickable elements have `cursor: pointer`
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Focus states visible for keyboard nav (orange outline)
- [ ] Touch targets ≥ 44x44px

### Color & Contrast
- [ ] Text contrast 4.5:1 minimum (`--ink` on `--bg` ✓)
- [ ] Borders visible (`--border` on light bg ✓)
- [ ] CTA stands out (`--orange` on white/mint ✓)
- [ ] `prefers-reduced-motion` respected

### Layout
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] No horizontal scroll on mobile
- [ ] Floating elements have proper spacing from edges
- [ ] No content hidden behind fixed navbars
