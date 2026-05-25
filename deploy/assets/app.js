/* =====================================================================
   Kfar-Link App.js v3 — לוגיקה משותפת לכל הדפים
   העברה 1:1 של הלוגיקה העסקית מ-app.py
   ===================================================================== */
(function() {
  'use strict';

  const KL = window.KL = {};

  // ====== STORAGE ======
  KL.storage = {
    get(key, defaultValue = null) {
      try {
        const v = localStorage.getItem('kl_' + key);
        return v ? JSON.parse(v) : defaultValue;
      } catch (e) { return defaultValue; }
    },
    set(key, value) {
      try { localStorage.setItem('kl_' + key, JSON.stringify(value)); }
      catch (e) { console.warn('Storage failed', e); }
    },
    remove(key) { localStorage.removeItem('kl_' + key); }
  };

  // ====== USER ======
  KL.user = {
    get current() { return KL.storage.get('user'); },
    isLoggedIn() { return !!this.current; },
    save(userData) { KL.storage.set('user', { ...userData, joinedAt: Date.now() }); },
    logout() {
      if (!confirm('להתנתק מכפר-לינק? תצטרכו להירשם מחדש.')) return;
      ['user','deals','myDeals','myJobs','myEvents','my_jobs','my_events','my_rides','my_shareItems'].forEach(k => KL.storage.remove(k));
      window.location.href = 'landing.html';
    },
    initials() {
      const u = this.current;
      if (!u || !u.name) return '?';
      const parts = u.name.trim().split(/\s+/);
      return (parts[0]?.[0] || '') + (parts[1]?.[0] || '');
    },
    firstName() {
      const u = this.current;
      if (!u || !u.name) return '';
      return u.name.trim().split(/\s+/)[0];
    },
    phone() { return this.current?.phone || ''; }
  };

  // ====== DEALS - מודל נתונים עשיר עם seed ראשוני ======
  KL.deals = {
    // טוען רכישות (כולל seed אם זה הפעם הראשונה)
    all() {
      let deals = KL.storage.get('deals', null);
      if (deals === null) {
        // SEED ראשוני - 4 רכישות דוגמה
        deals = this._seed();
        KL.storage.set('deals', deals);
      }
      return deals;
    },
    save(deals) { KL.storage.set('deals', deals); },
    findById(id) { return this.all().find(d => d.id === id); },
    update(id, updater) {
      const all = this.all();
      const idx = all.findIndex(d => d.id === id);
      if (idx === -1) return null;
      all[idx] = updater(all[idx]) || all[idx];
      this.save(all);
      return all[idx];
    },
    create(newDeal) {
      const all = this.all();
      all.unshift(newDeal); // חדש בהתחלה
      this.save(all);
      return newDeal;
    },
    _seed() {
      const today = new Date();
      const inDays = (n) => { const d = new Date(today); d.setDate(d.getDate() + n); return d.toISOString().slice(0,10); };
      return [
        {
          id: 'd_seed1', product_emoji: '🌾', name: 'מארז קמח אורגני 5 ק"ג', supplier: 'מטחנת אורגנית',
          price_retail: 13, box_size: 5, price_per_box: 38,
          business_address: 'אזור התעשייה כפר ויתקין', business_hours: 'א-ה 8:00-16:00', business_phone: '04-1234567',
          delivery_cost: 25, no_delivery: false,
          target_date: inDays(4),
          created_at: new Date(Date.now() - 86400000*2).toISOString(),
          status: 'open',
          organizer_name: 'נציג קהילה', organizer_phone: '050-1111111',
          carrier: null, comments: [],
          participants: [
            { id: 'p1', name: 'דנה לוי', phone: '0501111111', quantity: 5, need_expiry: inDays(4) },
            { id: 'p2', name: 'יוסי כהן', phone: '0502222222', quantity: 5, need_expiry: inDays(4) },
            { id: 'p3', name: 'מיכל אברהם', phone: '0503333333', quantity: 10, need_expiry: inDays(4) },
            { id: 'p4', name: 'אבי רוזן', phone: '0504444444', quantity: 5, need_expiry: inDays(4) },
            { id: 'p5', name: 'שירה ארד', phone: '0505555555', quantity: 5, need_expiry: inDays(4) },
            { id: 'p6', name: 'תום שביט', phone: '0506666666', quantity: 5, need_expiry: inDays(4) },
            { id: 'p7', name: 'נועה גרין', phone: '0507777777', quantity: 5, need_expiry: inDays(4) },
            { id: 'p8', name: 'רותם אסולין', phone: '0508888888', quantity: 5, need_expiry: inDays(4) },
            { id: 'p9', name: 'אורי בן-דוד', phone: '0509999999', quantity: 5, need_expiry: inDays(4) },
            { id: 'p10', name: 'הילה כהן', phone: '0501010101', quantity: 5, need_expiry: inDays(4) },
            { id: 'p11', name: 'יעל ארז', phone: '0502020202', quantity: 5, need_expiry: inDays(4) }
          ]
        },
        {
          id: 'd_seed2', product_emoji: '💧', name: 'מסנן מים מתחלף — PureFlow', supplier: 'PureFlow Israel',
          price_retail: 139, box_size: 1, price_per_box: 89,
          business_address: 'הברזל 22, תל אביב', business_hours: 'א-ו 9:00-18:00', business_phone: '03-7654321',
          delivery_cost: 30, no_delivery: false,
          target_date: inDays(3),
          created_at: new Date(Date.now() - 86400000).toISOString(),
          status: 'open',
          organizer_name: 'יוסי כהן', organizer_phone: '050-2222222',
          carrier: { name: 'יוסי כהן', phone: '050-2222222', type: 'with_discount' },
          comments: [],
          participants: [
            { id: 'p21', name: 'דנה לוי', phone: '0501111111', quantity: 1, need_expiry: inDays(3) },
            { id: 'p22', name: 'יוסי כהן', phone: '0502222222', quantity: 1, need_expiry: inDays(3), is_delivery_hero: true },
            { id: 'p23', name: 'מאיה שלום', phone: '0501212121', quantity: 1, need_expiry: inDays(3) },
            { id: 'p24', name: 'אורי בן-דוד', phone: '0509999999', quantity: 1, need_expiry: inDays(3) },
            { id: 'p25', name: 'הילה כהן', phone: '0501010101', quantity: 1, need_expiry: inDays(3) },
            { id: 'p26', name: 'תומר אביב', phone: '0501313131', quantity: 1, need_expiry: inDays(3) },
            { id: 'p27', name: 'רעות פרי', phone: '0501414141', quantity: 1, need_expiry: inDays(3) },
            { id: 'p28', name: 'אילן שריר', phone: '0501515151', quantity: 1, need_expiry: inDays(3) },
            { id: 'p29', name: 'נטע גרינברג', phone: '0501616161', quantity: 1, need_expiry: inDays(3) }
          ]
        },
        {
          id: 'd_seed3', product_emoji: '🫙', name: 'קופסאות זכוכית 800ml × 6', supplier: 'בית הזכוכית',
          price_retail: 16, box_size: 6, price_per_box: 62,
          business_address: 'אבן גבירול 50, רמת גן', business_hours: 'א-ו 9:00-19:00', business_phone: '03-1112222',
          delivery_cost: 20, no_delivery: false,
          target_date: inDays(4),
          created_at: new Date().toISOString(),
          status: 'open',
          organizer_name: 'שירה ארד', organizer_phone: '050-5555555',
          carrier: null, comments: [],
          participants: [
            { id: 'p31', name: 'שירה ארד', phone: '0505555555', quantity: 6, need_expiry: inDays(4) },
            { id: 'p32', name: 'תום שביט', phone: '0506666666', quantity: 6, need_expiry: inDays(4) },
            { id: 'p33', name: 'נועה גרין', phone: '0507777777', quantity: 6, need_expiry: inDays(4) },
            { id: 'p34', name: 'רותם אסולין', phone: '0508888888', quantity: 6, need_expiry: inDays(4) },
            { id: 'p35', name: 'אורי בן-דוד', phone: '0509999999', quantity: 6, need_expiry: inDays(4) }
          ]
        },
        {
          id: 'd_seed4', product_emoji: '🧺', name: 'סבון כביסה ביו-מסיס 3 ליטר', supplier: 'EcoClean',
          price_retail: 58, box_size: 3, price_per_box: 126,
          business_address: 'משלוח ישיר מהיצרן', business_hours: '', business_phone: '04-9876543',
          delivery_cost: 0, no_delivery: true,
          target_date: inDays(5),
          created_at: new Date(Date.now() - 86400000*3).toISOString(),
          status: 'open',
          organizer_name: 'אבי רוזן', organizer_phone: '050-4444444',
          carrier: { name: 'אבי רוזן', phone: '050-4444444', type: 'with_discount' },
          comments: [],
          participants: [
            { id: 'p41', name: 'אבי רוזן', phone: '0504444444', quantity: 3, need_expiry: inDays(5), is_delivery_hero: true },
            { id: 'p42', name: 'הילה כהן', phone: '0501010101', quantity: 3, need_expiry: inDays(5) },
            { id: 'p43', name: 'יעל ארז', phone: '0502020202', quantity: 3, need_expiry: inDays(5) },
            { id: 'p44', name: 'נטע גרינברג', phone: '0501616161', quantity: 3, need_expiry: inDays(5) },
            { id: 'p45', name: 'תומר אביב', phone: '0501313131', quantity: 3, need_expiry: inDays(5) },
            { id: 'p46', name: 'מאיה שלום', phone: '0501212121', quantity: 3, need_expiry: inDays(5) },
            { id: 'p47', name: 'רעות פרי', phone: '0501414141', quantity: 3, need_expiry: inDays(5) },
            { id: 'p48', name: 'אילן שריר', phone: '0501515151', quantity: 3, need_expiry: inDays(5) },
            { id: 'p49', name: 'נועה גרין', phone: '0507777777', quantity: 3, need_expiry: inDays(5) },
            { id: 'p50', name: 'דנה לוי', phone: '0501111111', quantity: 3, need_expiry: inDays(5) },
            { id: 'p51', name: 'שירה ארד', phone: '0505555555', quantity: 3, need_expiry: inDays(5) },
            { id: 'p52', name: 'תום שביט', phone: '0506666666', quantity: 3, need_expiry: inDays(5) },
            { id: 'p53', name: 'אורי בן-דוד', phone: '0509999999', quantity: 3, need_expiry: inDays(5) }
          ]
        }
      ];
    },
    // ====== חישוב מחיר דינמי - העברה 1:1 מ-app.py ======
    pricing(deal) {
      // הגבלה לארגז אחד בלבד - אם רוצים יותר, פותחים עסקה חדשה
      const box_size = deal.box_size;
      const target_price = Math.round((deal.price_per_box / box_size) * 100) / 100;
      if (!deal.participants || deal.participants.length === 0) {
        return { price_per_unit: deal.price_retail, target_price, total_units: 0, full_boxes: 0, units_to_next_box: box_size, units_remaining: box_size, units_leftover: box_size, total_cost: 0, savings_pct: 0, box_fill_ratio: 0, box_is_full: false };
      }
      const total_units = deal.participants.reduce((s, p) => s + (p.quantity || 0), 0);
      // עלות = ארגז אחד תמיד
      const total_cost = deal.price_per_box;
      const price_per_unit = total_cost / Math.max(1, total_units);
      const units_remaining = Math.max(0, box_size - total_units);
      const box_is_full = total_units >= box_size;
      const box_fill_ratio = Math.min(1, total_units / box_size);
      const savings_pct = Math.max(0, (deal.price_retail - price_per_unit) / deal.price_retail * 100);
      return {
        price_per_unit: Math.round(price_per_unit * 100) / 100,
        target_price, total_units,
        full_boxes: total_units > 0 ? 1 : 0,
        units_to_next_box: box_size,
        units_remaining,
        units_leftover: units_remaining,
        total_cost: Math.round(total_cost * 100) / 100,
        savings_pct: Math.round(savings_pct * 10) / 10,
        box_fill_ratio: Math.round(box_fill_ratio * 1000) / 1000,
        box_is_full
      };
    },
    // האם משתמש יכול להצטרף בכמות מסוימת?
    canJoin(deal, requestedQty) {
      const pricing = this.pricing(deal);
      return pricing.units_remaining >= requestedQty;
    },
    // ====== גיבור משלוח - 5% הנחה עד 20₪ ======
    heroInfo(deal, price_per_unit) {
      const HERO_DISCOUNT_RATE = 0.05;
      const HERO_DISCOUNT_CAP = 20.0;
      const heroes = (deal.participants || []).filter(p => p.is_delivery_hero);
      if (heroes.length === 0) return null;
      const hero = heroes[0];
      const original_cost = hero.quantity * price_per_unit;
      const discount = Math.min(original_cost * HERO_DISCOUNT_RATE, HERO_DISCOUNT_CAP);
      return {
        name: hero.name,
        phone: hero.phone,
        original_cost: Math.round(original_cost * 100) / 100,
        discount: Math.round(discount * 100) / 100,
        final_cost: Math.round((original_cost - discount) * 100) / 100
      };
    },
    // ====== פעולות משתמש ======
    isUserIn(deal) {
      const phone = KL.user.phone();
      return (deal.participants || []).some(p => p.phone === phone);
    },
    getUserParticipant(deal) {
      const phone = KL.user.phone();
      return (deal.participants || []).find(p => p.phone === phone);
    },
    join(dealId, quantity) {
      const u = KL.user.current;
      if (!u) return { ok: false, reason: 'not_logged_in' };
      const deal = this.findById(dealId);
      if (!deal) return { ok: false, reason: 'not_found' };
      if (!this.canJoin(deal, quantity)) {
        const pricing = this.pricing(deal);
        return { ok: false, reason: 'no_room', remaining: pricing.units_remaining };
      }
      this.update(dealId, d => {
        d.participants = d.participants || [];
        if (d.participants.find(p => p.phone === u.phone)) return d;
        d.participants.push({
          id: 'p_' + Date.now(),
          name: u.name, phone: u.phone,
          quantity: quantity,
          need_expiry: d.target_date
        });
        return d;
      });
      return { ok: true };
    },
    leave(dealId) {
      const u = KL.user.current;
      if (!u) return false;
      this.update(dealId, deal => {
        deal.participants = (deal.participants || []).filter(p => p.phone !== u.phone);
        // אם המשתמש היה carrier - הסר
        if (deal.carrier && deal.carrier.phone === u.phone) deal.carrier = null;
        return deal;
      });
      return true;
    },
    updateQuantity(dealId, newQty) {
      const u = KL.user.current;
      if (!u) return { ok: false };
      const deal = this.findById(dealId);
      if (!deal) return { ok: false };
      const myPart = (deal.participants || []).find(p => p.phone === u.phone);
      if (!myPart) return { ok: false };
      // בודק אם הכמות החדשה אפשרית
      const otherUnits = (deal.participants || []).reduce((s, p) => s + (p.phone === u.phone ? 0 : p.quantity), 0);
      if (otherUnits + newQty > deal.box_size) {
        return { ok: false, reason: 'no_room', max: deal.box_size - otherUnits };
      }
      this.update(dealId, d => {
        const p = (d.participants || []).find(p => p.phone === u.phone);
        if (p) p.quantity = newQty;
        return d;
      });
      return { ok: true };
    },
    // עריכת פרטי עסקה (רק מארגן)
    edit(dealId, updates) {
      const u = KL.user.current;
      if (!u) return false;
      const deal = this.findById(dealId);
      if (!deal || deal.organizer_phone !== u.phone) return false;
      this.update(dealId, d => Object.assign(d, updates));
      return true;
    },
    isOrganizer(deal) {
      return deal.organizer_phone === KL.user.phone();
    },
    isUserHero(deal) {
      const userP = this.getUserParticipant(deal);
      return !!(userP && userP.is_delivery_hero);
    },
    becomeCarrier(dealId, type) {
      const u = KL.user.current;
      if (!u) return false;
      this.update(dealId, deal => {
        deal.carrier = { name: u.name, phone: u.phone, type: type || 'with_discount' };
        // גם המשתמש מסומן כ-is_delivery_hero
        const p = (deal.participants || []).find(p => p.phone === u.phone);
        if (p) p.is_delivery_hero = true;
        return deal;
      });
      return true;
    },
    leaveCarrier(dealId) {
      const u = KL.user.current;
      if (!u) return false;
      this.update(dealId, deal => {
        if (deal.carrier && deal.carrier.phone === u.phone) deal.carrier = null;
        const p = (deal.participants || []).find(p => p.phone === u.phone);
        if (p) p.is_delivery_hero = false;
        return deal;
      });
      return true;
    },
    addComment(dealId, text) {
      this.update(dealId, deal => {
        deal.comments = deal.comments || [];
        deal.comments.push({
          id: 'c_' + Date.now(),
          author: KL.user.firstName(),
          text: text,
          at: new Date().toLocaleString('he-IL', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
        });
        return deal;
      });
    },
    // ימים שנותרו עד target_date
    daysRemaining(deal) {
      const target = new Date(deal.target_date);
      const now = new Date();
      return Math.max(0, Math.ceil((target - now) / 86400000));
    },
    statusInfo(deal) {
      const days = this.daysRemaining(deal);
      const total = (deal.participants || []).reduce((s, p) => s + p.quantity, 0);
      const pricing = this.pricing(deal);
      if (days === 0) return { label: 'נסגר', color: 'red', daysLeft: 0 };
      if (pricing.box_is_full) return { label: 'ארגז מלא ✓', color: 'green', daysLeft: days };
      if (days <= 1) return { label: 'מסתיים מחר!', color: 'orange', daysLeft: days };
      if (days <= 3) return { label: days + ' ימים נשארו', color: 'orange', daysLeft: days };
      return { label: days + ' ימים נשארו', color: 'blue', daysLeft: days };
    }
  };

  // ====== TOAST ======
  KL.toast = function(message, type, duration) {
    type = type || 'success';
    duration = duration || 3000;
    let host = document.getElementById('kl-toast-host');
    if (!host) { host = document.createElement('div'); host.id = 'kl-toast-host'; document.body.appendChild(host); }
    const el = document.createElement('div');
    el.className = 'kl-toast kl-toast-' + type;
    const icons = {
      success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
      info: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
      error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/></svg>'
    };
    el.innerHTML = '<span class="kl-toast-icon">' + (icons[type]||'') + '</span><span>' + message + '</span>';
    host.appendChild(el);
    requestAnimationFrame(() => el.classList.add('kl-toast-in'));
    setTimeout(() => { el.classList.remove('kl-toast-in'); el.classList.add('kl-toast-out'); setTimeout(() => el.remove(), 250); }, duration);
  };

  // ====== MODAL ======
  KL.modal = {
    open(opts) {
      this.close();
      const overlay = document.createElement('div');
      overlay.className = 'kl-modal-overlay';
      const cancelBtn = opts.hideCancel ? '' : '<button type="button" class="btn btn-ghost kl-modal-cancel">סגור</button>';
      const submitBtn = opts.hideSubmit ? '' : '<button type="submit" class="btn btn-green">' + (opts.submitLabel || 'אישור') + '</button>';
      const actions = (cancelBtn || submitBtn) ? '<div class="kl-modal-actions">' + cancelBtn + submitBtn + '</div>' : '';
      overlay.innerHTML = '<div class="kl-modal" role="dialog">' +
        '<button class="kl-modal-close" aria-label="סגירה"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></button>' +
        '<h3 class="kl-modal-title">' + (opts.title || '') + '</h3>' +
        '<form class="kl-modal-form" novalidate>' +
        '<div class="kl-modal-body">' + this._renderBody(opts) + '</div>' +
        actions +
        '</form></div>';
      document.body.appendChild(overlay);
      document.body.style.overflow = 'hidden';
      requestAnimationFrame(() => overlay.classList.add('kl-modal-in'));
      overlay.querySelector('.kl-modal-close').addEventListener('click', () => this.close());
      overlay.querySelector('.kl-modal-cancel')?.addEventListener('click', () => this.close());
      overlay.addEventListener('click', (e) => { if (e.target === overlay) this.close(); });
      document.addEventListener('keydown', this._escHandler = (e) => { if (e.key === 'Escape') this.close(); });
      overlay.querySelector('.kl-modal-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = {};
        overlay.querySelectorAll('[name]').forEach(input => {
          if (input.type === 'checkbox') formData[input.name] = input.checked;
          else formData[input.name] = input.value;
        });
        if (opts.onSubmit) opts.onSubmit(formData, () => this.close());
        else this.close();
      });
      const firstInput = overlay.querySelector('input, select, textarea');
      if (firstInput) setTimeout(() => firstInput.focus(), 150);
      if (opts.onMount) setTimeout(() => opts.onMount(overlay), 50);
    },
    close() {
      const overlay = document.querySelector('.kl-modal-overlay');
      if (overlay) { overlay.classList.remove('kl-modal-in'); overlay.classList.add('kl-modal-out'); setTimeout(() => overlay.remove(), 200); }
      document.body.style.overflow = '';
      if (this._escHandler) { document.removeEventListener('keydown', this._escHandler); this._escHandler = null; }
    },
    _renderBody(opts) {
      if (opts.body) return opts.body;
      if (!opts.fields) return '';
      return opts.fields.map(f => {
        const required = f.required ? 'required' : '';
        const optionalLabel = f.required === false ? '<span class="field-optional">אופציונלי</span>' : '';
        const hint = f.hint ? '<span class="hint">' + f.hint + '</span>' : '';
        if (f.type === 'select') {
          return '<div class="field"><label>' + f.label + ' ' + optionalLabel + '</label>' +
            '<select class="select" name="' + f.name + '" ' + required + '>' +
            (f.placeholder ? '<option value="">' + f.placeholder + '</option>' : '') +
            f.options.map(o => '<option value="' + (o.value || o) + '"' + (f.value === (o.value || o) ? ' selected' : '') + '>' + (o.label || o) + '</option>').join('') +
            '</select>' + hint + '</div>';
        }
        if (f.type === 'textarea') {
          return '<div class="field"><label>' + f.label + ' ' + optionalLabel + '</label>' +
            '<textarea class="textarea" name="' + f.name + '" placeholder="' + (f.placeholder || '') + '" ' + required + '>' + (f.value || '') + '</textarea>' + hint + '</div>';
        }
        if (f.type === 'checkbox') {
          return '<label class="check"><input type="checkbox" name="' + f.name + '" ' + (f.value ? 'checked' : '') + '/><span class="check-body"><span class="check-title">' + f.label + '</span>' + (f.hint ? '<span class="check-sub">' + f.hint + '</span>' : '') + '</span></label>';
        }
        return '<div class="field"><label>' + f.label + ' ' + optionalLabel + '</label>' +
          '<input class="input" type="' + (f.type || 'text') + '" name="' + f.name + '" placeholder="' + (f.placeholder || '') + '" value="' + (f.value !== undefined ? f.value : '') + '" ' + required + (f.inputmode ? ' inputmode="' + f.inputmode + '"' : '') + (f.min !== undefined ? ' min="' + f.min + '"' : '') + (f.max !== undefined ? ' max="' + f.max + '"' : '') + (f.step !== undefined ? ' step="' + f.step + '"' : '') + ' /></div>';
      }).join('');
    }
  };

  // ====== UI ======
  KL.ui = {
    updateNavAvatar() {
      document.querySelectorAll('.nav-user .avatar').forEach(a => { a.textContent = KL.user.initials(); });
    },
    addLogoutButton() {
      document.querySelectorAll('.nav-user').forEach(nav => {
        if (nav.querySelector('.kl-logout-btn')) return;
        if (!KL.user.isLoggedIn()) return;
        const btn = document.createElement('button');
        btn.className = 'btn btn-ghost btn-sm kl-logout-btn';
        btn.title = 'התנתקות';
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>';
        btn.addEventListener('click', () => KL.user.logout());
        nav.insertBefore(btn, nav.firstChild);
      });
    }
  };

  // ====== AUTO-INIT ======
  document.addEventListener('DOMContentLoaded', () => {
    KL.ui.updateNavAvatar();
    KL.ui.addLogoutButton();
    const welcomeH1 = document.querySelector('.welcome-hero h1');
    if (welcomeH1 && KL.user.isLoggedIn()) {
      const hour = new Date().getHours();
      const greeting = hour < 12 ? 'בוקר טוב' : (hour < 18 ? 'אחר צהריים טובים' : 'ערב טוב');
      welcomeH1.innerHTML = greeting + ', ' + KL.user.firstName() + ' 🌱';
    }
  });
})();
