"""
═══════════════════════════════════════════════════════════════
 MabiliSSS Queue V1.1.0 — COMBINED PORTAL (Single Process)
 Member + Staff in ONE app — guaranteed data sync.
 Run: streamlit run mabilisss.py --server.port 8501
 © RPT / SSS Gingoog Branch 2026
═══════════════════════════════════════════════════════════════
"""

import streamlit as st
import json, os, time, uuid, csv, io
from datetime import datetime, date
from pathlib import Path

# ═══════════════════════════════════════════════════
#  DATA LAYER (embedded — no external imports)
# ═══════════════════════════════════════════════════
VER = "V1.1.0"
_DIR = Path(__file__).resolve().parent / "data"
_DIR.mkdir(exist_ok=True)

def _qf(d=None):
    return _DIR / f"queue_{d or date.today().isoformat()}.json"

def _r(path, default):
    if not path.exists():
        _w(path, default)
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def _w(path, data):
    tmp = str(path) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    os.replace(tmp, str(path))

BRANCH_F = _DIR / "branch.json"
CATS_F   = _DIR / "categories.json"
USERS_F  = _DIR / "users.json"

DEF_BRANCH = {
    "name": "SSS Gingoog Branch",
    "address": "National Highway, Gingoog City",
    "hours": "Mon-Fri, 8:00 AM - 5:00 PM",
    "phone": "", "openTime": "06:00", "closeTime": "16:00",
    "bqmsStartTime": "08:00", "announcement": "",
}

DEF_CATS = [
    {"id":"ret_death","label":"Retirement / Death / Funeral","icon":"🏖️","short":"Ret/Death","avgTime":16,"cap":50,
     "services":[{"id":"retirement","label":"Retirement Claim"},{"id":"death_claim","label":"Death Claim"},{"id":"funeral","label":"Funeral Benefit"}]},
    {"id":"smd","label":"Sickness / Maternity / Disability","icon":"🏥","short":"Sick/Mat","avgTime":14,"cap":50,
     "services":[{"id":"sickness","label":"Sickness Benefit"},{"id":"maternity","label":"Maternity / Paternity"},{"id":"disability","label":"Disability Benefit"}]},
    {"id":"loans","label":"Loans","icon":"💰","short":"Loans","avgTime":10,"cap":60,
     "services":[{"id":"salary_loan","label":"Salary Loan"},{"id":"calamity_loan","label":"Calamity Loan"},{"id":"emergency_loan","label":"Emergency Loan"},{"id":"consoloan","label":"Consoloan"}]},
    {"id":"membership","label":"Membership / ID / Inquiries","icon":"🪪","short":"Members","avgTime":8,"cap":60,
     "services":[{"id":"new_member","label":"New Registration"},{"id":"umid","label":"UMID Enrollment / Release"},{"id":"e1_update","label":"E-1 / E-4 Update"},{"id":"inquiry","label":"General Inquiry"},{"id":"member_record","label":"Member Records"}]},
    {"id":"acop","label":"ACOP","icon":"📋","short":"ACOP","avgTime":10,"cap":30,
     "services":[{"id":"acop_filing","label":"ACOP Filing"},{"id":"acop_followup","label":"ACOP Follow-up"}]},
    {"id":"payments","label":"Payments","icon":"💳","short":"Payments","avgTime":7,"cap":70,
     "services":[{"id":"pay_contribution","label":"Contribution Payment"},{"id":"pay_loan","label":"Loan Amortization"},{"id":"pay_others","label":"Other Payments / PRN"}]},
    {"id":"employers","label":"Employers","icon":"🏢","short":"Employers","avgTime":12,"cap":30,
     "services":[{"id":"er_registration","label":"Employer Registration"},{"id":"er_reporting","label":"Collection / Reporting"},{"id":"er_inquiry","label":"Employer Inquiry"},{"id":"er_certificate","label":"Employer Certification"}]},
]

DEF_USERS = [
    {"id":"kiosk","username":"kiosk","displayName":"Guard / Kiosk","role":"kiosk","password":"mnd2026","active":True},
    {"id":"staff1","username":"staff1","displayName":"Staff 1","role":"staff","password":"mnd2026","active":True},
    {"id":"staff2","username":"staff2","displayName":"Staff 2","role":"staff","password":"mnd2026","active":True},
    {"id":"th","username":"th","displayName":"Team Head","role":"th","password":"mnd2026","active":True},
    {"id":"bh","username":"bh","displayName":"Branch Head","role":"bh","password":"mnd2026","active":True},
    {"id":"dh","username":"dh","displayName":"Division Head","role":"dh","password":"mnd2026","active":True},
]

def get_branch():     return _r(BRANCH_F, DEF_BRANCH)
def save_branch(d):   _w(BRANCH_F, d)
def get_cats():       return _r(CATS_F, DEF_CATS)
def save_cats(d):     _w(CATS_F, d)
def get_users():      return _r(USERS_F, DEF_USERS)
def save_users(d):    _w(USERS_F, d)
def get_queue(d=None):
    return _r(_qf(d), {"res":[], "bqmsState":{}, "oStat":"online", "date": d or date.today().isoformat()})
def save_queue(data, d=None):
    data["date"] = d or date.today().isoformat()
    _w(_qf(d), data)

def slot_counts(cats, res_list):
    m = {}
    for c in cats:
        active = [r for r in res_list if r.get("categoryId") == c["id"] and r.get("status") != "NO_SHOW"]
        m[c["id"]] = {"used": len(active), "cap": c.get("cap",50), "remaining": max(0, c.get("cap",50) - len(active))}
    return m

def next_slot(res_list):
    return len(res_list) + 1

def is_dup(res_list, last, first, mob):
    nk = f"{last}|{first}"
    for r in res_list:
        if r.get("status") in ("NO_SHOW","COMPLETED"): continue
        if f"{r.get('lastName','')}|{r.get('firstName','')}" == nk: return True
        if mob and r.get("mobile") and r["mobile"] == mob: return True
    return False

def gen_id():
    return f"{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}"

def mmdd():
    return date.today().strftime("%m%d")

OSTATUS = {
    "online":       {"label":"Reservation Open",             "emoji":"🟢","color":"green"},
    "intermittent": {"label":"Intermittent - Expect Delays", "emoji":"🟡","color":"yellow"},
    "offline":      {"label":"Reservation Closed",           "emoji":"🔴","color":"red"},
}

# ═══════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════
st.set_page_config(page_title="MabiliSSS Queue", page_icon="🏛️", layout="centered")

# ── CSS ──
st.markdown("""<style>
.sss-header{background:linear-gradient(135deg,#002E52,#0066A1);color:#fff!important;padding:18px 22px;border-radius:12px;margin-bottom:16px}
.sss-header h2{margin:0;font-size:22px;color:#fff!important}
.sss-header p{margin:4px 0 0;opacity:.75;font-size:13px;color:#fff!important}
.sss-card{background:var(--secondary-background-color,#fff);color:var(--text-color,#1a1a2e);border-radius:10px;padding:16px;margin-bottom:12px;border:1px solid rgba(128,128,128,.15)}
.sss-card strong,.sss-card b{color:var(--text-color,#1a1a2e)}
.sss-metric{text-align:center;padding:14px 8px;border-radius:10px;background:var(--secondary-background-color,#f5f5f5);border:1px solid rgba(128,128,128,.1)}
.sss-metric .val{font-size:30px;font-weight:900;line-height:1.2}
.sss-metric .lbl{font-size:11px;opacity:.6;margin-top:2px}
.sss-alert{border-radius:8px;padding:12px 16px;margin-bottom:12px;font-weight:600;text-align:center}
.sss-alert-red{background:rgba(220,53,69,.15);color:#ef4444;border:1px solid rgba(220,53,69,.3)}
.sss-alert-green{background:rgba(15,157,88,.12);color:#22c55e;border:1px solid rgba(15,157,88,.25)}
.sss-alert-blue{background:rgba(59,130,246,.12);color:#60a5fa;border:1px solid rgba(59,130,246,.25)}
.sss-alert-yellow{background:rgba(217,119,6,.12);color:#f59e0b;border:1px solid rgba(217,119,6,.25)}
.sss-alert strong,.sss-alert b{color:inherit}
.sss-badge{display:inline-block;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700}
.sss-bqms{font-family:monospace;font-size:36px;font-weight:900;color:#22B8CF;text-align:center}
.sss-resnum{font-family:monospace;font-size:26px;font-weight:900;color:#3399CC;text-align:center}
.sss-card td{color:var(--text-color,#1a1a2e);padding:4px 0}
.sss-card td.muted{opacity:.6}
.stButton>button{border-radius:8px;font-weight:700}
</style>""", unsafe_allow_html=True)

# ── Auto-refresh ──
_ar_ok = False
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15_000, limit=None, key="global_ar")
    _ar_ok = True
except ImportError:
    pass

# ── Session defaults ──
for k, v in {"portal":"member","screen":"home","sel_cat":None,"sel_svc":None,
             "ticket":None,"tracked_id":None,"auth_user":None,"fail_count":0,
             "lock_until":0,"staff_tab":"queue","last_activity":time.time()}.items():
    if k not in st.session_state:
        st.session_state[k] = v

now = datetime.now()

# ── PORTAL SWITCHER (sidebar) ──
with st.sidebar:
    st.markdown("### 🏛️ MabiliSSS Queue")
    portal = st.radio("Portal:", ["👤 Member Portal", "🔐 Staff Portal"],
                       index=0 if st.session_state.portal == "member" else 1)
    st.session_state.portal = "member" if "Member" in portal else "staff"
    st.markdown("---")
    # DIAGNOSTIC — ALWAYS VISIBLE
    q_diag = get_queue()
    b_diag = get_branch()
    st.markdown(f"""**🔗 Live Data Status**
- 📂 `{_DIR}`
- 📄 `{_qf().name}`
- 📊 **{len(q_diag.get('res',[]))} entries**
- 🚦 oStat: **{q_diag.get('oStat','?')}**
- 📢 Ann: {'✅' if b_diag.get('announcement','').strip() else '—'}
- 🔄 Auto-refresh: {'✅ 15s' if _ar_ok else '❌'}""")
    if not _ar_ok:
        st.warning("Install: `pip install streamlit-autorefresh`")
    if st.button("🔄 Manual Refresh", use_container_width=True):
        st.rerun()
    st.caption(f"Last render: {now.strftime('%I:%M:%S %p')}")

def go(scr):
    st.session_state.screen = scr
    st.rerun()

# ════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════
#  MEMBER PORTAL
# ════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════
if st.session_state.portal == "member":
    branch = get_branch()
    cats   = get_cats()
    qdata  = get_queue()
    res    = qdata.get("res", [])
    bqms_st= qdata.get("bqmsState", {})
    o_stat = qdata.get("oStat", "online")
    is_open= o_stat != "offline"
    sc     = slot_counts(cats, res)

    # Header
    st.markdown(f"""<div class="sss-header">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><h2>🏛️ MabiliSSS Queue</h2><p>{branch['name']} · {VER}</p></div>
            <div style="text-align:right;font-size:13px;opacity:.8;">
                {now.strftime('%A, %b %d, %Y')}<br/>{now.strftime('%I:%M %p')}</div>
        </div></div>""", unsafe_allow_html=True)

    # Status bar
    sm = OSTATUS.get(o_stat, OSTATUS["online"])
    st.markdown(f"""<div class="sss-alert sss-alert-{sm['color']}" style="font-size:15px;">
        <strong>{sm['emoji']} {sm['label']}</strong></div>""", unsafe_allow_html=True)

    # Announcement
    _ann = branch.get("announcement","").strip()
    if _ann:
        st.markdown(f"""<div style="position:sticky;top:0;z-index:999;
            background:linear-gradient(90deg,#002E52,#0066A1);
            color:#fff;padding:10px 0;margin-bottom:12px;border-radius:8px;overflow:hidden;
            box-shadow:0 2px 8px rgba(0,0,0,.15);">
            <div style="display:inline-block;white-space:nowrap;
                animation:sss-scroll 18s linear infinite;font-weight:700;font-size:14px;">
                📢&nbsp;&nbsp;{_ann}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                📢&nbsp;&nbsp;{_ann}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                📢&nbsp;&nbsp;{_ann}
            </div></div>
        <style>@keyframes sss-scroll{{0%{{transform:translateX(0%)}}100%{{transform:translateX(-33.33%)}}}}</style>""",
        unsafe_allow_html=True)

    screen = st.session_state.screen

    # ── HOME ──
    if screen == "home":
        active_q = len([r for r in res if r.get("status") not in ("COMPLETED","NO_SHOW")])
        done_q   = len([r for r in res if r.get("status") == "COMPLETED"])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="sss-metric"><div class="val" style="color:#3399CC;">{active_q}</div><div class="lbl">Active Queue</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="sss-metric"><div class="val" style="color:#22c55e;">{done_q}</div><div class="lbl">Served Today</div></div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📋 Reserve a Slot", use_container_width=True, type="primary", disabled=not is_open):
                st.session_state.sel_cat = None; st.session_state.sel_svc = None
                go("select_cat")
        with c2:
            if st.button("🔍 Track My Queue", use_container_width=True):
                st.session_state.tracked_id = None
                go("track_input")

        if not is_open:
            st.warning("Reservation is currently closed.")

        st.markdown(f"""<div class="sss-card" style="border-left:4px solid #f59e0b;">
            <strong>📌 How It Works</strong><br/><br/>
            1. Tap <b>"Reserve a Slot"</b> and fill in your details.<br/>
            2. Go to {branch['name']} during office hours.<br/>
            3. Present your reservation to the guard.<br/>
            4. Staff assigns your <b>official BQMS queue number</b>.<br/>
            5. Tap <b>"Track My Queue"</b> to monitor live!
        </div>""", unsafe_allow_html=True)

    # ── SELECT CATEGORY ──
    elif screen == "select_cat":
        if st.button("← Back to Home"): go("home")
        st.subheader("Step 1: Choose Transaction")
        for cat in cats:
            s = sc.get(cat["id"], {"remaining": cat["cap"]})
            full = s["remaining"] <= 0
            c1, c2 = st.columns([5, 1])
            with c1:
                if st.button(f"{cat['icon']} {cat['label']}", key=f"cat_{cat['id']}", disabled=full, use_container_width=True):
                    st.session_state.sel_cat = cat["id"]; go("select_svc")
            with c2:
                if full:
                    st.error("FULL")
                else:
                    st.markdown(f"<div style='text-align:center;'><span style='font-size:20px;font-weight:900;color:#3399CC;'>{s['remaining']}</span><br/><span style='font-size:10px;opacity:.5;'>left</span></div>", unsafe_allow_html=True)

    # ── SELECT SERVICE ──
    elif screen == "select_svc":
        cat = next((c for c in cats if c["id"] == st.session_state.sel_cat), None)
        if not cat: go("select_cat")
        else:
            if st.button("← Back"): go("select_cat")
            st.subheader(f"Step 2: {cat['icon']} {cat['short']}")
            for svc in cat.get("services", []):
                if st.button(f"● {svc['label']}", key=f"svc_{svc['id']}", use_container_width=True):
                    st.session_state.sel_svc = svc["id"]; go("member_form")

    # ── MEMBER FORM ──
    elif screen == "member_form":
        cat = next((c for c in cats if c["id"] == st.session_state.sel_cat), None)
        svc = None
        if cat:
            svc = next((s for s in cat.get("services",[]) if s["id"] == st.session_state.sel_svc), None)
        if not cat or not svc: go("select_cat")
        else:
            if st.button("← Back"): go("select_svc")
            st.subheader("Step 3: Your Details")
            st.markdown(f'<div class="sss-card">{cat["icon"]} <strong>{svc["label"]}</strong><br/><span style="opacity:.6;">{cat["label"]}</span></div>', unsafe_allow_html=True)

            with st.form("reserve_form"):
                fc1, fc2 = st.columns(2)
                with fc1: last_name = st.text_input("Last Name *", placeholder="DELA CRUZ")
                with fc2: first_name = st.text_input("First Name *", placeholder="JUAN")
                fc1, fc2 = st.columns([1,3])
                with fc1: mi = st.text_input("M.I.", max_chars=2)
                with fc2: mobile = st.text_input("Mobile *", placeholder="09XX XXX XXXX")
                pri = st.radio("Lane:", ["👤 Regular", "⭐ Priority (Senior/PWD/Pregnant)"], horizontal=True)
                pri_type = "priority" if "Priority" in pri else "regular"
                st.markdown("**🔒 Data Privacy (RA 10173)**")
                consent = st.checkbox("I consent to data collection for today's queue.")

                if st.form_submit_button("📋 Reserve My Slot", type="primary", use_container_width=True):
                    lu = last_name.strip().upper(); fu = first_name.strip().upper(); mob = mobile.strip()
                    fresh = get_queue(); fr = fresh.get("res",[])
                    errors = []
                    if not lu: errors.append("Last Name required.")
                    if not fu: errors.append("First Name required.")
                    if not mob or len(mob) < 10: errors.append("Valid mobile required.")
                    if not consent: errors.append("Check privacy consent.")
                    fsc = slot_counts(cats, fr)
                    if fsc.get(cat["id"],{}).get("remaining",0) <= 0: errors.append("Slots full.")
                    if is_dup(fr, lu, fu, mob): errors.append("Duplicate reservation.")

                    if errors:
                        for e in errors: st.error(f"❌ {e}")
                    else:
                        slot = next_slot(fr)
                        rn = f"R-{mmdd()}-{slot:03d}"
                        entry = {
                            "id": gen_id(), "slot": slot, "resNum": rn,
                            "lastName": lu, "firstName": fu, "mi": mi.strip().upper(),
                            "mobile": mob, "service": svc["label"], "serviceId": svc["id"],
                            "category": cat["label"], "categoryId": cat["id"],
                            "catIcon": cat["icon"], "priority": pri_type,
                            "status": "RESERVED", "bqmsNumber": None,
                            "source": "ONLINE", "issuedAt": now.isoformat(),
                            "arrivedAt": None, "completedAt": None,
                        }
                        fr.append(entry); fresh["res"] = fr; save_queue(fresh)
                        st.session_state.ticket = entry; go("ticket")

    # ── TICKET ──
    elif screen == "ticket":
        t = st.session_state.ticket
        if not t: go("home")
        else:
            st.markdown(f'<div style="text-align:center;"><span style="font-size:48px;">✅</span><h2 style="color:#22c55e;">Slot Reserved!</h2></div>', unsafe_allow_html=True)
            st.markdown(f"""<div class="sss-card" style="border-top:4px solid #3399CC;text-align:center;">
                <div style="font-size:11px;opacity:.5;letter-spacing:2px;">MABILISSS QUEUE — {branch['name'].upper()}</div>
                <div style="font-weight:700;margin:4px 0;">{t['category']} — {t['service']}</div>
                <hr style="border:1px dashed rgba(128,128,128,.2);"/>
                <div style="font-size:11px;opacity:.5;">RESERVATION NUMBER</div>
                <div class="sss-resnum">{t['resNum']}</div>
                <hr style="border:1px dashed rgba(128,128,128,.2);"/>
                <div style="font-size:12px;">{t['lastName']}, {t['firstName']} {t.get('mi','')}<br/>📱 {t['mobile']}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""<div class="sss-card" style="border-left:4px solid #3399CC;">
                <strong>📋 Next Steps:</strong><br/>
                1. Save: <code style="font-size:16px;font-weight:900;">{t['resNum']}</code><br/>
                2. Go to <strong>{branch['name']}</strong><br/>
                3. Present to guard → get <strong>BQMS number</strong><br/>
                4. Tap <strong>"Track My Queue"</strong> anytime!
            </div>""", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("🏠 Home", use_container_width=True):
                    st.session_state.ticket = None; go("home")
            with c2:
                if st.button("🔍 Track Now", use_container_width=True, type="primary"):
                    st.session_state.tracked_id = t["id"]; go("tracker")

    # ── TRACK INPUT ──
    elif screen == "track_input":
        if st.button("← Back to Home"): go("home")
        st.markdown('<div style="text-align:center;"><span style="font-size:36px;">🔍</span><h3>Track Your Queue</h3></div>', unsafe_allow_html=True)
        st.caption("💡 Online = **R-** prefix (R-0214-001). Walk-in/kiosk = **K-** prefix (K-0214-001).")

        track_mode = st.radio("Search by:", ["📱 Mobile Number", "#️⃣ Reservation Number"], horizontal=True)
        with st.form("track_form"):
            if "Mobile" in track_mode:
                track_val = st.text_input("Mobile number", placeholder="09XX XXX XXXX")
            else:
                track_val = st.text_input("Reservation #", placeholder="R-0214-005 or K-0214-001")

            if st.form_submit_button("🔍 Find My Queue", type="primary", use_container_width=True):
                fresh = get_queue(); fr = fresh.get("res",[])
                v = track_val.strip()
                if not v:
                    st.error("Enter a value.")
                else:
                    found = None
                    if "Mobile" in track_mode:
                        for r in fr:
                            if r.get("mobile") == v and r.get("status") not in ("COMPLETED","NO_SHOW"):
                                found = r; break
                        if not found:
                            for r in fr:
                                if r.get("mobile") == v: found = r; break
                    else:
                        vu = v.upper()
                        for r in fr:
                            if r.get("resNum") == vu and r.get("status") not in ("COMPLETED","NO_SHOW"):
                                found = r; break
                        if not found:
                            for r in fr:
                                if r.get("resNum") == vu: found = r; break
                    if not found:
                        st.error(f"❌ Not found for '{v}'. Check input.")
                        # Debug: show what's in queue
                        if fr:
                            st.caption(f"Queue has {len(fr)} entries: {', '.join(r.get('resNum','?') for r in fr[:10])}")
                        else:
                            st.caption("Queue is empty — no entries today.")
                    else:
                        st.session_state.tracked_id = found["id"]; go("tracker")

    # ── TRACKER ──
    elif screen == "tracker":
        tid = st.session_state.tracked_id
        fresh = get_queue(); fr = fresh.get("res",[]); fbq = fresh.get("bqmsState",{})
        t = next((r for r in fr if r.get("id") == tid), None)
        if not t:
            st.error("❌ Entry not found.")
            if st.button("← Try Again"): go("track_input")
        else:
            has_bqms = bool(t.get("bqmsNumber"))
            is_done  = t.get("status") == "COMPLETED"
            is_ns    = t.get("status") == "NO_SHOW"
            is_srv   = t.get("status") == "SERVING"

            if is_srv:
                st.markdown('<div class="sss-alert sss-alert-blue" style="font-size:18px;">🎉 <strong>YOU\'RE BEING SERVED!</strong></div>', unsafe_allow_html=True)
            elif is_done:
                st.markdown(f'<div class="sss-alert sss-alert-green">✅ <strong>Completed</strong> — Thank you!</div>', unsafe_allow_html=True)
            elif is_ns:
                st.markdown('<div class="sss-alert sss-alert-red">❌ <strong>No-Show</strong></div>', unsafe_allow_html=True)

            _sl = {"RESERVED":"📋 RESERVED","ARRIVED":"✅ ARRIVED","SERVING":"🔵 SERVING","COMPLETED":"✅ DONE","NO_SHOW":"❌ NO-SHOW"}
            st.markdown(f"""<div class="sss-card" style="border-top:4px solid {'#22B8CF' if has_bqms else '#3399CC'};text-align:center;">
                <div style="font-size:11px;opacity:.5;">{branch['name'].upper()}</div>
                <div style="font-weight:700;margin:4px 0;">{t['category']} — {t['service']}</div>
                <span class="sss-badge" style="background:rgba(51,153,204,.15);color:#3399CC;">{_sl.get(t['status'],t['status'])}</span>
            </div>""", unsafe_allow_html=True)

            if has_bqms:
                st.markdown(f'<div class="sss-card" style="text-align:center;"><div style="font-size:11px;opacity:.5;">YOUR BQMS NUMBER</div><div class="sss-bqms">{t["bqmsNumber"]}</div></div>', unsafe_allow_html=True)
                if not is_done and not is_ns:
                    cat_obj = next((c for c in cats if c["id"] == t.get("categoryId")), None)
                    bq = fbq.get(t.get("categoryId",""),{})
                    ns_val = bq.get("nowServing","—")
                    avg = cat_obj["avgTime"] if cat_obj else 10
                    ahead = 0
                    try:
                        ns_num = int("".join(filter(str.isdigit, str(ns_val))))
                        my_num = int("".join(filter(str.isdigit, str(t["bqmsNumber"]))))
                        ahead = max(0, my_num - ns_num)
                    except: pass
                    est = ahead * avg
                    m1,m2,m3 = st.columns(3)
                    with m1: st.markdown(f'<div class="sss-metric"><div class="val" style="color:#22B8CF;">{ns_val}</div><div class="lbl">Now Serving</div></div>', unsafe_allow_html=True)
                    with m2: st.markdown(f'<div class="sss-metric"><div class="val">{t["bqmsNumber"]}</div><div class="lbl">Your #</div></div>', unsafe_allow_html=True)
                    with m3:
                        wt = "Next!" if est == 0 else f"~{est}m"
                        st.markdown(f'<div class="sss-metric"><div class="val">{wt}</div><div class="lbl">Est. Wait</div></div>', unsafe_allow_html=True)
            else:
                if not is_done and not is_ns:
                    st.markdown(f'<div class="sss-card" style="text-align:center;"><div style="font-size:11px;opacity:.5;">RESERVATION NUMBER</div><div class="sss-resnum">{t["resNum"]}</div></div>', unsafe_allow_html=True)
                    st.markdown('<div class="sss-alert sss-alert-yellow">⏳ <strong>Waiting for BQMS Number</strong><br/>Staff will assign. Auto-refreshes.</div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 Refresh", use_container_width=True, type="primary"): st.rerun()
            with c2:
                if st.button("🔍 Track Another", use_container_width=True):
                    st.session_state.tracked_id = None; go("track_input")


# ════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════
#  STAFF PORTAL
# ════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════
elif st.session_state.portal == "staff":

    # ── Session timeout ──
    if st.session_state.auth_user and (time.time() - st.session_state.last_activity > 30 * 60):
        st.session_state.auth_user = None
        st.warning("Session expired.")

    # ── LOGIN ──
    if not st.session_state.auth_user:
        st.markdown('<div class="sss-header" style="text-align:center;"><span style="font-size:36px;">🔐</span><h2>Staff Portal</h2><p>Authorized Personnel Only</p></div>', unsafe_allow_html=True)
        locked = time.time() < st.session_state.lock_until
        if locked:
            st.error(f"🔒 Locked. Wait {int(st.session_state.lock_until - time.time())}s.")
        with st.form("login"):
            username = st.text_input("Username", placeholder="staff1, kiosk, th, bh")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login", type="primary", use_container_width=True, disabled=locked):
                users = get_users()
                u = next((x for x in users if x["username"].lower() == username.strip().lower() and x.get("active",True)), None)
                if not u:
                    st.error("❌ User not found.")
                elif u["password"] != password:
                    st.session_state.fail_count += 1
                    left = 3 - st.session_state.fail_count
                    if left <= 0:
                        st.session_state.lock_until = time.time() + 300
                        st.session_state.fail_count = 0
                        st.error("❌ Locked 5 min.")
                    else:
                        st.error(f"❌ Wrong password. {left} left.")
                else:
                    st.session_state.auth_user = u
                    st.session_state.fail_count = 0
                    st.session_state.staff_tab = "queue"
                    st.session_state.last_activity = time.time()
                    st.rerun()
        st.caption("Default password: **mnd2026**")
        st.stop()

    # ── AUTHENTICATED ──
    st.session_state.last_activity = time.time()
    user = st.session_state.auth_user
    role = user["role"]
    branch = get_branch()
    cats   = get_cats()
    users  = get_users()
    qdata  = get_queue()
    res    = qdata.get("res", [])
    bqms_st= qdata.get("bqmsState", {})
    o_stat = qdata.get("oStat", "online")
    sc     = slot_counts(cats, res)
    is_ro  = role in ("bh","dh")

    ROLE_ICONS = {"kiosk":"🏢","staff":"🛡️","th":"👔","bh":"🏛️","dh":"⭐"}
    ROLE_LABELS = {"kiosk":"Kiosk","staff":"Staff","th":"Team Head","bh":"Branch Head","dh":"Division Head"}

    st.markdown(f"""<div class="sss-header">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><h2>{ROLE_ICONS.get(role,'')} Staff Console</h2>
                <p>{user['displayName']} · {ROLE_LABELS.get(role,role)}</p></div>
            <div style="text-align:right;font-size:12px;opacity:.8;">{now.strftime('%I:%M %p')}<br/>{date.today().isoformat()}</div>
        </div></div>""", unsafe_allow_html=True)

    # ── Nav ──
    nav = [("📋 Queue","queue")]
    if role == "th": nav.append(("👔 Admin","admin"))
    if role in ("th","bh","dh"): nav.append(("📊 Dashboard","dash"))
    nav += [("🔑 Password","pw"),("🚪 Logout","logout")]
    cols = st.columns(len(nav))
    for i,(lbl,key) in enumerate(nav):
        with cols[i]:
            if key == "logout":
                if st.button(lbl, use_container_width=True):
                    st.session_state.auth_user = None; st.rerun()
            else:
                bt = "primary" if st.session_state.staff_tab == key else "secondary"
                if st.button(lbl, use_container_width=True, type=bt):
                    st.session_state.staff_tab = key; st.rerun()

    tab = st.session_state.staff_tab

    # ── PASSWORD ──
    if tab == "pw":
        st.subheader("🔑 Change Password")
        with st.form("pw_form"):
            np1 = st.text_input("New Password", type="password")
            np2 = st.text_input("Confirm", type="password")
            if st.form_submit_button("Save", type="primary"):
                if len(np1) < 4: st.error("Min 4 chars.")
                elif np1 != np2: st.error("Mismatch.")
                else:
                    all_u = get_users()
                    for u in all_u:
                        if u["id"] == user["id"]: u["password"] = np1
                    save_users(all_u)
                    st.session_state.auth_user["password"] = np1
                    st.success("✅ Changed!"); st.session_state.staff_tab = "queue"; st.rerun()

    # ══════════════════════════════════════════
    #  QUEUE CONSOLE
    # ══════════════════════════════════════════
    elif tab == "queue":
        # Live indicator
        st.caption(f"🔄 Live · {len(res)} entries · Auto: {'✅ 15s' if _ar_ok else '❌'} · {now.strftime('%I:%M:%S %p')}")

        unassigned = [r for r in res if not r.get("bqmsNumber") and r.get("status") not in ("NO_SHOW","COMPLETED")]

        if not is_ro:
            # System status
            st.markdown("**System Status**")
            _sopts = ["🟢 Online","🟡 Intermittent","🔴 Offline"]
            _smap  = {"🟢 Online":"online","🟡 Intermittent":"intermittent","🔴 Offline":"offline"}
            _srev  = {v:k for k,v in _smap.items()}
            cur_lbl= _srev.get(o_stat, "🟢 Online")
            new_s  = st.radio("Status:", _sopts, horizontal=True, index=_sopts.index(cur_lbl))
            if _smap[new_s] != o_stat:
                fq = get_queue(); fq["oStat"] = _smap[new_s]; save_queue(fq); st.rerun()

            # Announcement
            if role != "kiosk":
                with st.expander(f"📢 Announcement {'(ACTIVE)' if branch.get('announcement','').strip() else '(none)'}"):
                    with st.form("ann_form"):
                        ann_text = st.text_area("Shows as scrolling banner on member app", value=branch.get("announcement",""), height=80)
                        ac1, ac2 = st.columns([3,1])
                        with ac1: ann_save = st.form_submit_button("📢 Post", type="primary")
                        with ac2: ann_clr = st.form_submit_button("🗑️ Clear")
                        if ann_save:
                            fb = get_branch(); fb["announcement"] = ann_text.strip(); save_branch(fb)
                            st.success("✅ Posted!"); st.rerun()
                        if ann_clr:
                            fb = get_branch(); fb["announcement"] = ""; save_branch(fb)
                            st.success("✅ Cleared!"); st.rerun()

            # Unassigned alert
            if unassigned:
                st.markdown(f'<div class="sss-alert sss-alert-red" style="font-size:16px;">🔴 <strong>{len(unassigned)} NEED BQMS#</strong></div>', unsafe_allow_html=True)

            # BQMS Now Serving
            with st.expander("🔄 BQMS — Now Serving"):
                with st.form("bqms_form"):
                    new_bqms = dict(bqms_st)
                    for i in range(0, len(cats), 2):
                        cols2 = st.columns(2)
                        for j, col in enumerate(cols2):
                            idx = i + j
                            if idx >= len(cats): break
                            c = cats[idx]
                            with col:
                                cur = bqms_st.get(c["id"],{}).get("nowServing","")
                                val = st.text_input(f"{c['icon']} {c['short']}", value=cur, key=f"bqms_{c['id']}")
                                new_bqms[c["id"]] = {"nowServing": val.strip().upper()}
                    if st.form_submit_button("Update", type="primary", use_container_width=True):
                        fq = get_queue(); fq["bqmsState"] = new_bqms; save_queue(fq)
                        st.success("✅ Updated!"); st.rerun()

            # Walk-in registration
            with st.expander("➕ Add Walk-in"):
                with st.form("walkin"):
                    cat_labels = ["-- Select --"] + [f"{c['icon']} {c['label']} ({sc.get(c['id'],{}).get('remaining',0)} left)" for c in cats]
                    w_cat_i = st.selectbox("Category *", range(len(cat_labels)), format_func=lambda i: cat_labels[i])
                    w_cat = cats[w_cat_i - 1] if w_cat_i > 0 else None
                    # Services for selected category
                    if w_cat:
                        svc_labels = ["-- None --"] + [s["label"] for s in w_cat.get("services",[])]
                        w_svc_i = st.selectbox("Sub-service", range(len(svc_labels)), format_func=lambda i: svc_labels[i])
                        w_svc = w_cat["services"][w_svc_i-1] if w_svc_i > 0 else None
                    else:
                        w_svc = None
                    wc1,wc2 = st.columns(2)
                    with wc1: wl = st.text_input("Last Name *", key="wl")
                    with wc2: wf = st.text_input("First Name *", key="wf")
                    wc1,wc2 = st.columns([1,3])
                    with wc1: wmi = st.text_input("M.I.", max_chars=2, key="wmi")
                    with wc2: wmob = st.text_input("Mobile (optional)", key="wmob")
                    wpri = st.radio("Lane:", ["👤 Regular","⭐ Priority"], horizontal=True, key="wpri")
                    wbqms = ""
                    if role != "kiosk":
                        wbqms = st.text_input("BQMS # (if issued)", placeholder="Leave blank if not yet", key="wbqms")

                    if st.form_submit_button("Register Walk-in", type="primary", use_container_width=True):
                        wlu = wl.strip().upper(); wfu = wf.strip().upper(); wmu = wmob.strip()
                        errs = []
                        if not w_cat: errs.append("Select category.")
                        if not wlu: errs.append("Last Name required.")
                        if not wfu: errs.append("First Name required.")
                        if errs:
                            for e in errs: st.error(f"❌ {e}")
                        else:
                            fresh = get_queue(); fr = fresh.get("res",[])
                            fsc = slot_counts(cats, fr)
                            if is_dup(fr, wlu, wfu, wmu):
                                st.error("Duplicate.")
                            elif fsc.get(w_cat["id"],{}).get("remaining",0) <= 0:
                                st.error("Cap reached.")
                            else:
                                slot = next_slot(fr)
                                rn = f"K-{mmdd()}-{slot:03d}"
                                bv = wbqms.strip().upper() if wbqms else ""
                                svc_lbl = w_svc["label"] if w_svc else "Walk-in"
                                svc_id  = w_svc["id"] if w_svc else "walkin"
                                entry = {
                                    "id": gen_id(), "slot": slot, "resNum": rn,
                                    "lastName": wlu, "firstName": wfu,
                                    "mi": wmi.strip().upper(), "mobile": wmu,
                                    "service": svc_lbl, "serviceId": svc_id,
                                    "category": w_cat["label"], "categoryId": w_cat["id"],
                                    "catIcon": w_cat["icon"],
                                    "priority": "priority" if "Priority" in wpri else "regular",
                                    "status": "ARRIVED" if bv else "RESERVED",
                                    "bqmsNumber": bv or None,
                                    "source": "KIOSK", "issuedAt": now.isoformat(),
                                    "arrivedAt": now.isoformat() if bv else None,
                                    "completedAt": None,
                                }
                                fr.append(entry); fresh["res"] = fr; save_queue(fresh)
                                st.success(f"✅ **{rn}** — Share this number with the member for tracking!")
                                st.rerun()

        # ── QUEUE LIST ──
        st.markdown("---")
        _fm = {"🔴 Need BQMS":"UNASSIGNED","All":"all","🏢 Kiosk":"KIOSK","📱 Online":"ONLINE","✅ Arrived":"ARRIVED","✔ Done":"COMPLETED","❌ No-Show":"NO_SHOW"}
        sel_f = st.radio("Filter:", list(_fm.keys()), horizontal=True, index=0)
        qf = _fm[sel_f]
        search = st.text_input("🔍 Search", key="qsearch")

        sorted_res = sorted(res, key=lambda r: (0 if not r.get("bqmsNumber") and r.get("status") not in ("NO_SHOW","COMPLETED") else 1, r.get("issuedAt","")))
        filt = sorted_res
        if qf == "UNASSIGNED": filt = [r for r in filt if not r.get("bqmsNumber") and r.get("status") not in ("NO_SHOW","COMPLETED")]
        elif qf == "KIOSK": filt = [r for r in filt if r.get("source") == "KIOSK"]
        elif qf == "ONLINE": filt = [r for r in filt if r.get("source") == "ONLINE"]
        elif qf != "all": filt = [r for r in filt if r.get("status") == qf]
        if search:
            sl = search.strip().lower()
            filt = [r for r in filt if sl in r.get("lastName","").lower() or sl in r.get("firstName","").lower() or sl in (r.get("bqmsNumber","") or "").lower() or sl in (r.get("resNum","") or "").lower()]

        st.caption(f"Showing {len(filt)} entries")

        if not filt:
            if qf == "UNASSIGNED": st.success("✅ All have BQMS#!")
            else: st.info("No entries.")
        else:
            for r in filt:
                needs_b = not r.get("bqmsNumber") and r.get("status") not in ("NO_SHOW","COMPLETED")
                bdr = "#ef4444" if needs_b else "rgba(128,128,128,.15)"
                src = "🏢" if r.get("source") == "KIOSK" else "📱"
                pri = "⭐" if r.get("priority") == "priority" else ""
                _sl = {"RESERVED":"📋 RES","ARRIVED":"✅ ARR","SERVING":"🔵 SRV","COMPLETED":"✅ DONE","NO_SHOW":"❌ NS"}
                bqms_h = f'<div style="font-family:monospace;font-size:20px;font-weight:900;color:#22B8CF;margin-top:4px;">BQMS: {r["bqmsNumber"]}</div>' if r.get("bqmsNumber") else ""

                st.markdown(f"""<div class="sss-card" style="border-left:4px solid {bdr};">
                    <div style="display:flex;justify-content:space-between;">
                        <div><span style="font-family:monospace;font-size:15px;font-weight:800;color:#3399CC;">{r.get('resNum','')}</span>
                            <span style="font-size:11px;opacity:.5;margin-left:6px;">{src}</span>{pri}<br/>
                            <strong>{r.get('catIcon','')} {r['lastName']}, {r['firstName']} {r.get('mi','')}</strong><br/>
                            <span style="font-size:12px;opacity:.6;">{r.get('category','')} → {r.get('service','')}</span>
                            {f'<br/><span style="font-size:11px;opacity:.5;">📱 {r["mobile"]}</span>' if r.get('mobile') else ''}
                        </div>
                        <div style="text-align:right;"><span class="sss-badge" style="background:rgba(51,153,204,.15);color:#3399CC;">{_sl.get(r['status'],r['status'])}</span>{bqms_h}</div>
                    </div></div>""", unsafe_allow_html=True)

                if not is_ro:
                    if needs_b:
                        st.markdown(f"""<div style="background:rgba(220,53,69,.08);border:1px solid rgba(220,53,69,.25);border-radius:8px;padding:10px 14px;margin-bottom:8px;">
                            <span style="font-size:12px;font-weight:700;color:#ef4444;">🎫 Assign BQMS for {r.get('resNum','')}</span><br/>
                            <span style="font-size:11px;opacity:.6;">Type number from the physical BQMS machine</span></div>""", unsafe_allow_html=True)
                        ac1,ac2 = st.columns([3,1])
                        with ac1: bv = st.text_input(f"BQMS# for {r.get('resNum','')}", key=f"a_{r['id']}", placeholder="e.g., L-023")
                        with ac2:
                            st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
                            if st.button("🎫 Assign", key=f"ba_{r['id']}", type="primary", use_container_width=True):
                                if bv.strip():
                                    fq = get_queue()
                                    for fr in fq["res"]:
                                        if fr["id"] == r["id"]:
                                            fr["bqmsNumber"] = bv.strip().upper()
                                            fr["status"] = "ARRIVED"
                                            fr["arrivedAt"] = now.isoformat()
                                    save_queue(fq); st.rerun()
                                else:
                                    st.warning("Enter BQMS# first.")
                        if st.button("❌ No-Show", key=f"ns_{r['id']}", use_container_width=True):
                            fq = get_queue()
                            for fr in fq["res"]:
                                if fr["id"] == r["id"]: fr["status"] = "NO_SHOW"
                            save_queue(fq); st.rerun()

                    elif r.get("status") == "ARRIVED":
                        ac1,ac2,ac3 = st.columns(3)
                        with ac1:
                            if st.button("🔵 Serving", key=f"srv_{r['id']}", use_container_width=True):
                                fq = get_queue()
                                for fr in fq["res"]:
                                    if fr["id"] == r["id"]: fr["status"] = "SERVING"
                                save_queue(fq); st.rerun()
                        with ac2:
                            if st.button("✅ Complete", key=f"dn_{r['id']}", use_container_width=True):
                                fq = get_queue()
                                for fr in fq["res"]:
                                    if fr["id"] == r["id"]: fr["status"] = "COMPLETED"; fr["completedAt"] = now.isoformat()
                                save_queue(fq); st.rerun()
                        with ac3:
                            if st.button("❌ NS", key=f"ns2_{r['id']}", use_container_width=True):
                                fq = get_queue()
                                for fr in fq["res"]:
                                    if fr["id"] == r["id"]: fr["status"] = "NO_SHOW"
                                save_queue(fq); st.rerun()

                    elif r.get("status") == "SERVING":
                        if st.button("✅ Complete", key=f"dn2_{r['id']}", type="primary", use_container_width=True):
                            fq = get_queue()
                            for fr in fq["res"]:
                                if fr["id"] == r["id"]: fr["status"] = "COMPLETED"; fr["completedAt"] = now.isoformat()
                            save_queue(fq); st.rerun()
                st.markdown("")

        st.markdown("---")
        if st.button("🔄 Refresh Queue", use_container_width=True): st.rerun()

    # ── ADMIN ──
    elif tab == "admin" and role == "th":
        st.subheader("👔 Admin Panel")
        atabs = st.tabs(["👥 Users","📋 Categories","📊 Caps","🏢 Branch","📢 Announcement"])

        with atabs[0]:
            for u in users:
                rl = ROLE_LABELS.get(u["role"], u["role"])
                st.markdown(f"**{u['displayName']}** — {rl} · `{u['username']}` · {'🟢' if u.get('active',True) else '🔴'}")

        with atabs[1]:
            for cat in cats:
                svcs = ", ".join(s["label"] for s in cat.get("services",[]))
                st.markdown(f"**{cat['icon']} {cat['label']}** — Cap: {cat['cap']} · Avg: {cat['avgTime']}m")
                st.caption(f"  Services: {svcs}")

        with atabs[2]:
            with st.form("caps"):
                new_caps = {}
                for cat in cats:
                    s = sc.get(cat["id"],{"used":0})
                    new_caps[cat["id"]] = st.number_input(f"{cat['icon']} {cat['short']} (used: {s['used']})", value=cat["cap"], min_value=1, key=f"cap_{cat['id']}")
                if st.form_submit_button("Save Caps", type="primary"):
                    fc = get_cats()
                    for c in fc:
                        if c["id"] in new_caps: c["cap"] = new_caps[c["id"]]
                    save_cats(fc); st.success("✅ Saved!"); st.rerun()

        with atabs[3]:
            with st.form("branch"):
                bn = st.text_input("Name", value=branch["name"])
                ba = st.text_input("Address", value=branch["address"])
                bh = st.text_input("Hours", value=branch["hours"])
                if st.form_submit_button("Save", type="primary"):
                    fb = get_branch(); fb.update({"name":bn,"address":ba,"hours":bh}); save_branch(fb)
                    st.success("✅ Saved!"); st.rerun()

        with atabs[4]:
            with st.form("ann2"):
                ann = st.text_area("📢 Announcement", value=branch.get("announcement",""))
                if st.form_submit_button("Save", type="primary"):
                    fb = get_branch(); fb["announcement"] = ann; save_branch(fb)
                    st.success("✅ Saved!"); st.rerun()

    # ── DASHBOARD ──
    elif tab == "dash" and role in ("th","bh","dh"):
        st.subheader("📊 Dashboard")
        tot = len(res); done = len([r for r in res if r.get("status")=="COMPLETED"])
        ns = len([r for r in res if r.get("status")=="NO_SHOW"])
        onl = len([r for r in res if r.get("source")=="ONLINE"])
        ksk = len([r for r in res if r.get("source")=="KIOSK"])

        c1,c2,c3 = st.columns(3)
        with c1: st.metric("Total", tot)
        with c2: st.metric("Completed", done)
        with c3: st.metric("No-Show", ns)
        c1,c2 = st.columns(2)
        with c1: st.metric("📱 Online", onl)
        with c2: st.metric("🏢 Kiosk", ksk)

        if tot:
            st.metric("📱 Online Adoption", f"{onl/tot*100:.0f}%")
            st.metric("❌ No-Show Rate", f"{ns/tot*100:.1f}%")

        # CSV Export
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["Res#","Source","LastName","FirstName","Category","Service","Status","BQMS#","Mobile","Priority"])
        for r in res:
            w.writerow([r.get("resNum",""),r.get("source",""),r.get("lastName",""),r.get("firstName",""),r.get("category",""),r.get("service",""),r.get("status",""),r.get("bqmsNumber",""),r.get("mobile",""),r.get("priority","")])
        st.download_button("📥 Export CSV", data=out.getvalue(), file_name=f"MabiliSSS_{date.today().isoformat()}.csv", mime="text/csv", use_container_width=True)

# ── FOOTER ──
st.markdown("---")
st.markdown(f"""<div style="text-align:center;font-size:10px;opacity:.3;padding:8px;">
    RPT / SSS Gingoog Branch · MabiliSSS Queue {VER} · 📂 {_DIR}
</div>""", unsafe_allow_html=True)
