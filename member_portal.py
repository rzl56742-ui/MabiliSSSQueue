"""
═══════════════════════════════════════════════════════════════
 MabiliSSS Queue V1.0.0 — MEMBER PORTAL (Streamlit)
 Reserve & Track — No login required.
 Run: streamlit run member_portal.py --server.port 8501
 © RPT / SSS Gingoog Branch 2026
═══════════════════════════════════════════════════════════════
"""

import streamlit as st
from datetime import datetime
from shared_data import (
    VER, SSS_CSS, OSTATUS_META,
    get_branch, get_categories, get_queue, save_queue,
    slot_counts, next_slot_num, is_duplicate, gen_id,
    today_iso, today_mmdd, format_time_12h,
)

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="MabiliSSS Queue - Reserve",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(SSS_CSS, unsafe_allow_html=True)

# ── SESSION STATE ──
_DEFAULTS = {
    "screen": "home",
    "sel_cat": None,
    "sel_svc": None,
    "ticket": None,
    "tracked_id": None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── LOAD DATA (fresh every render) ──
branch = get_branch()
cats   = get_categories()
qdata  = get_queue()
res    = qdata.get("res", [])
bqms_st= qdata.get("bqmsState", {})
o_stat = qdata.get("oStat", "online")
is_open= o_stat != "offline"
sc     = slot_counts(cats, res)
now    = datetime.now()

def go(scr):
    st.session_state.screen = scr
    st.rerun()


# ═══════════════════════════════════════════════════
#  AUTO-REFRESH — ALL SCREENS (status, BQMS, announcements)
# ═══════════════════════════════════════════════════
_autorefresh_ok = False
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=20_000, limit=None, key="member_autorefresh")
    _autorefresh_ok = True
except ImportError:
    pass  # manual Refresh still available; warning shown below


# ═══════════════════════════════════════════════════
#  HEADER (always shown)
# ═══════════════════════════════════════════════════
st.markdown(f"""<div class="sss-header">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div><h2>🏛️ MabiliSSS Queue</h2><p>{branch['name']} · {VER}</p></div>
        <div style="text-align:right;font-size:13px;opacity:0.8;">
            {now.strftime('%A, %b %d, %Y')}<br/>{now.strftime('%I:%M %p')}
        </div>
    </div>
</div>""", unsafe_allow_html=True)

# ── STATUS BAR ──
sm = OSTATUS_META.get(o_stat, OSTATUS_META["online"])
_acls = {"online":"green","intermittent":"yellow","offline":"red"}
st.markdown(f"""<div class="sss-alert sss-alert-{_acls.get(o_stat,'green')}"
    style="font-size:15px;"><strong>{sm['emoji']} {sm['label']}</strong></div>""",
    unsafe_allow_html=True)

# ── STICKY SCROLLING ANNOUNCEMENT ──
_ann = branch.get("announcement", "").strip()
if _ann:
    st.markdown(f"""
    <div style="
        position: sticky; top: 0; z-index: 999;
        background: linear-gradient(90deg, #002E52, #0066A1);
        color: #FFFFFF; padding: 10px 0; margin-bottom: 12px;
        border-radius: 8px; overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    ">
        <div style="
            display: inline-block; white-space: nowrap;
            animation: sss-scroll 18s linear infinite;
            font-weight: 700; font-size: 14px;
        ">
            📢&nbsp;&nbsp;{_ann}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            📢&nbsp;&nbsp;{_ann}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            📢&nbsp;&nbsp;{_ann}
        </div>
    </div>
    <style>
        @keyframes sss-scroll {{
            0%   {{ transform: translateX(0%); }}
            100% {{ transform: translateX(-33.33%); }}
        }}
    </style>
    """, unsafe_allow_html=True)

if not _autorefresh_ok:
    st.warning("⚠️ Auto-refresh not installed. Tap Refresh to see updates.")
    if st.button("🔄 Refresh Page", type="primary", use_container_width=True, key="member_manual_refresh"):
        st.rerun()


screen = st.session_state.screen


# ═══════════════════════════════════════════════════
#  HOME
# ═══════════════════════════════════════════════════
if screen == "home":
    active_q = len([r for r in res if r.get("status") not in ("COMPLETED","NO_SHOW")])
    done_q   = len([r for r in res if r.get("status") == "COMPLETED"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="sss-metric">
            <div class="val" style="color:#3399CC;">{active_q}</div>
            <div class="lbl">Active Queue</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="sss-metric">
            <div class="val" style="color:#22c55e;">{done_q}</div>
            <div class="lbl">Served Today</div></div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📋 Reserve a Slot", use_container_width=True, type="primary",
                      disabled=not is_open):
            st.session_state.sel_cat = None
            st.session_state.sel_svc = None
            go("select_cat")
    with c2:
        if st.button("🔍 Track My Queue", use_container_width=True):
            st.session_state.tracked_id = None
            go("track_input")

    if not is_open:
        st.warning("Reservation is currently closed. Visit the branch or try again later.")

    st.markdown(f"""<div class="sss-card" style="border-left:4px solid #f59e0b;">
        <strong>📌 Paano Gamitin (How It Works)</strong><br/><br/>
        1. Tap <b>"Reserve a Slot"</b> and fill in your details.<br/>
        2. Go to {branch['name']} during office hours.<br/>
        3. Present your reservation to the guard.<br/>
        4. Staff assigns your <b>official BQMS queue number</b>.<br/>
        5. Tap <b>"Track My Queue"</b> to monitor live!
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div class="sss-card">
            <strong>🔒 Privacy</strong><br/>
            <span style="opacity:0.6;font-size:12px;">RA 10173 compliant. Data for today only.</span>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="sss-card">
            <strong>⏰ Schedule</strong><br/>
            <span style="opacity:0.6;font-size:12px;">{branch['hours']}<br/>
            BQMS: {format_time_12h(branch.get('bqmsStartTime','08:00'))}</span>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  SELECT CATEGORY
# ═══════════════════════════════════════════════════
elif screen == "select_cat":
    if st.button("← Back to Home"):
        go("home")
    st.subheader("Step 1: Choose Transaction")

    for cat in cats:
        s = sc.get(cat["id"], {"remaining": cat["cap"], "cap": cat["cap"]})
        full = s["remaining"] <= 0
        c1, c2 = st.columns([5, 1])
        with c1:
            lbl = f"{cat['icon']} {cat['label']} ({len(cat.get('services',[]))} types)"
            if st.button(lbl, key=f"cat_{cat['id']}", disabled=full,
                         use_container_width=True):
                st.session_state.sel_cat = cat["id"]
                go("select_svc")
        with c2:
            if full:
                st.error("FULL")
            else:
                st.markdown(f"<div style='text-align:center;'>"
                    f"<span style='font-size:20px;font-weight:900;color:#3399CC;'>{s['remaining']}</span>"
                    f"<br/><span style='font-size:10px;opacity:0.5;'>left</span></div>",
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  SELECT SERVICE
# ═══════════════════════════════════════════════════
elif screen == "select_svc":
    cat = next((c for c in cats if c["id"] == st.session_state.sel_cat), None)
    if not cat:
        go("select_cat")
    else:
        if st.button("← Back"):
            go("select_cat")
        st.subheader(f"Step 2: {cat['icon']} {cat['short']}")
        st.caption("Select your specific transaction:")

        for svc in cat.get("services", []):
            if st.button(f"● {svc['label']}", key=f"svc_{svc['id']}",
                         use_container_width=True):
                st.session_state.sel_svc = svc["id"]
                go("member_form")


# ═══════════════════════════════════════════════════
#  MEMBER FORM
# ═══════════════════════════════════════════════════
elif screen == "member_form":
    cat = next((c for c in cats if c["id"] == st.session_state.sel_cat), None)
    svc = None
    if cat:
        svc = next((s for s in cat.get("services",[]) if s["id"] == st.session_state.sel_svc), None)
    if not cat or not svc:
        go("select_cat")
    else:
        if st.button("← Back"):
            go("select_svc")
        st.subheader("Step 3: Your Details")
        st.markdown(f"""<div class="sss-card">{cat['icon']}
            <strong>{svc['label']}</strong><br/>
            <span style="opacity:0.6;">{cat['label']}</span></div>""",
            unsafe_allow_html=True)

        with st.form("reserve_form"):
            st.markdown("**👤 Member Information**")
            fc1, fc2 = st.columns(2)
            with fc1:
                last_name = st.text_input("Last Name *", placeholder="e.g., DELA CRUZ")
            with fc2:
                first_name = st.text_input("First Name *", placeholder="e.g., JUAN")
            fc1, fc2 = st.columns([1, 3])
            with fc1:
                mi = st.text_input("M.I.", max_chars=2, placeholder="M")
            with fc2:
                mobile = st.text_input("Mobile Number *", placeholder="09XX XXX XXXX")

            st.markdown("---")
            pri = st.radio(
                "Queue Lane:",
                ["👤 Regular", "⭐ Priority (Senior/PWD/Pregnant)"],
                horizontal=True, index=0,
            )
            pri_type = "priority" if "Priority" in pri else "regular"
            if pri_type == "priority":
                st.warning("Senior 60+, PWD, Pregnant, Solo Parent ONLY. "
                           "Non-qualifiers will be moved to end of regular line.")

            st.markdown("---")
            st.markdown("**🔒 Data Privacy Consent (RA 10173)**")
            st.caption(
                f"Your name and mobile number are collected solely for today's "
                f"queue management at {branch['name']}. Data will not be shared "
                f"or retained beyond the business day."
            )
            consent = st.checkbox("I consent to the collection and use of my data.")

            submitted = st.form_submit_button("📋 Reserve My Slot", type="primary",
                                               use_container_width=True)
            if submitted:
                last_up  = last_name.strip().upper()
                first_up = first_name.strip().upper()
                mob      = mobile.strip()

                # Re-read fresh data to prevent race conditions
                fresh     = get_queue()
                fresh_res = fresh.get("res", [])
                fresh_sc  = slot_counts(cats, fresh_res)

                errors = []
                if not last_up:     errors.append("Last Name is required.")
                if not first_up:    errors.append("First Name is required.")
                if not mob or len(mob) < 10:
                    errors.append("Valid mobile number required (min 10 digits).")
                if not consent:     errors.append("Please check the privacy consent.")
                s = fresh_sc.get(cat["id"], {"remaining":0, "used":0})
                if s["remaining"] <= 0:
                    errors.append(f"Slots full for {cat['label']}.")
                if is_duplicate(fresh_res, last_up, first_up, mob):
                    errors.append("You already have an active reservation today.")

                if errors:
                    for e in errors:
                        st.error(f"❌ {e}")
                else:
                    slot = next_slot_num(fresh_res)
                    rn   = f"R-{today_mmdd()}-{slot:03d}"
                    entry = {
                        "id": gen_id(), "slot": slot, "resNum": rn,
                        "lastName": last_up, "firstName": first_up,
                        "mi": mi.strip().upper(), "mobile": mob,
                        "service": svc["label"], "serviceId": svc["id"],
                        "category": cat["label"], "categoryId": cat["id"],
                        "catIcon": cat["icon"], "priority": pri_type,
                        "status": "RESERVED", "bqmsNumber": None,
                        "source": "ONLINE",
                        "issuedAt": datetime.now().isoformat(),
                        "arrivedAt": None, "completedAt": None,
                    }
                    fresh_res.append(entry)
                    fresh["res"] = fresh_res
                    save_queue(fresh)
                    st.session_state.ticket = entry
                    go("ticket")


# ═══════════════════════════════════════════════════
#  TICKET CONFIRMATION
# ═══════════════════════════════════════════════════
elif screen == "ticket":
    t = st.session_state.ticket
    if not t:
        go("home")
    else:
        st.markdown("""<div style="text-align:center;margin:8px 0;">
            <span style="font-size:48px;">✅</span>
            <h2 style="color:#22c55e;margin:4px 0;">Slot Reserved!</h2>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="sss-card" style="border-top:4px solid #3399CC; text-align:center;">
            <div style="font-size:11px;opacity:0.5;letter-spacing:2px;">
                MABILISSS QUEUE — {branch['name'].upper()}</div>
            <div style="font-weight:700;margin:4px 0;">{t['category']} — {t['service']}</div>
            <hr style="border:1px dashed rgba(128,128,128,0.2);"/>
            <div style="font-size:11px;opacity:0.5;">RESERVATION NUMBER</div>
            <div class="sss-resnum">{t['resNum']}</div>
            <hr style="border:1px dashed rgba(128,128,128,0.2);"/>
            <table style="width:100%;font-size:13px;">
                <tr><td class="muted" style="text-align:left;">Name</td>
                    <td style="text-align:right;font-weight:700;">{t['lastName']}, {t['firstName']} {t['mi']}</td></tr>
                <tr><td class="muted" style="text-align:left;">Mobile</td>
                    <td style="text-align:right;font-weight:700;">{t['mobile']}</td></tr>
                <tr><td class="muted" style="text-align:left;">Lane</td>
                    <td style="text-align:right;font-weight:700;">
                        {'⭐ Priority' if t['priority']=='priority' else '👤 Regular'}</td></tr>
            </table>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="sss-card" style="border-left:4px solid #3399CC;">
            <strong>📋 Next Steps:</strong><br/><br/>
            1. Save your number: <code style="font-size:16px;font-weight:900;">{t['resNum']}</code><br/>
            2. Go to <strong>{branch['name']}</strong><br/>
            3. Present to guard / info desk<br/>
            4. Get your <strong>official BQMS number</strong><br/>
            5. Tap <strong>"Track My Queue"</strong> anytime!
        </div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.ticket = None
                go("home")
        with c2:
            if st.button("🔍 Track Now", use_container_width=True, type="primary"):
                st.session_state.tracked_id = t["id"]
                go("tracker")


# ═══════════════════════════════════════════════════
#  TRACK INPUT
# ═══════════════════════════════════════════════════
elif screen == "track_input":
    if st.button("← Back to Home"):
        go("home")

    st.markdown("""<div style="text-align:center;margin:8px 0;">
        <span style="font-size:36px;">🔍</span>
        <h3>Track Your Queue</h3>
        <p style="opacity:0.6;">See your live BQMS number and wait time.</p>
    </div>""", unsafe_allow_html=True)
    st.caption("💡 Online reservations start with **R-** (e.g., R-0214-001). "
               "Walk-in / kiosk numbers start with **K-** (e.g., K-0214-001).")

    track_mode = st.radio("Search by:", ["📱 Mobile Number", "#️⃣ Reservation Number"],
                          horizontal=True)

    with st.form("track_form"):
        if "Mobile" in track_mode:
            track_val = st.text_input("Mobile number", placeholder="09XX XXX XXXX")
        else:
            track_val = st.text_input("Reservation number", placeholder="e.g., R-0214-005 or K-0214-001")

        if st.form_submit_button("🔍 Find My Queue", type="primary",
                                  use_container_width=True):
            fresh     = get_queue()
            fresh_res = fresh.get("res", [])
            v = track_val.strip().upper()
            if not v:
                st.error("Please enter a value.")
            else:
                found = None
                if "Mobile" in track_mode:
                    v_raw = track_val.strip()
                    # Prefer active match, fallback to any
                    for r in fresh_res:
                        if r.get("mobile") == v_raw and r.get("status") not in ("COMPLETED","NO_SHOW"):
                            found = r; break
                    if not found:
                        for r in fresh_res:
                            if r.get("mobile") == v_raw:
                                found = r; break
                else:
                    for r in fresh_res:
                        if r.get("resNum") == v and r.get("status") not in ("COMPLETED","NO_SHOW"):
                            found = r; break
                    if not found:
                        for r in fresh_res:
                            if r.get("resNum") == v:
                                found = r; break

                if not found:
                    st.error("❌ Not found. Check your input and try again.")
                else:
                    st.session_state.tracked_id = found["id"]
                    go("tracker")


# ═══════════════════════════════════════════════════
#  LIVE TRACKER  (auto-refreshes via streamlit_autorefresh)
# ═══════════════════════════════════════════════════
elif screen == "tracker":
    tid = st.session_state.tracked_id
    fresh     = get_queue()
    fresh_res = fresh.get("res", [])
    fresh_bq  = fresh.get("bqmsState", {})

    t = next((r for r in fresh_res if r.get("id") == tid), None)
    if not t:
        st.error("❌ Entry not found.")
        if st.button("← Try Again"):
            go("track_input")
    else:
        has_bqms   = bool(t.get("bqmsNumber"))
        is_done    = t.get("status") == "COMPLETED"
        is_ns      = t.get("status") == "NO_SHOW"
        is_serving = t.get("status") == "SERVING"

        # Status banners
        if is_serving:
            st.markdown("""<div class="sss-alert sss-alert-blue" style="font-size:18px;">
                🎉 <strong>YOU'RE BEING SERVED!</strong><br/>
                Proceed to the counter now.
            </div>""", unsafe_allow_html=True)
        elif is_done:
            st.markdown(f"""<div class="sss-alert sss-alert-green">
                ✅ <strong>Completed</strong><br/>
                Thank you for visiting {branch['name']}!
            </div>""", unsafe_allow_html=True)
        elif is_ns:
            st.markdown("""<div class="sss-alert sss-alert-red">
                ❌ <strong>No-Show</strong><br/>
                Please create a new reservation.
            </div>""", unsafe_allow_html=True)

        # Main info card
        _slabels = {
            "RESERVED":"📋 RESERVED", "ARRIVED":"✅ ARRIVED",
            "SERVING":"🔵 NOW SERVING", "COMPLETED":"✅ DONE", "NO_SHOW":"❌ NO-SHOW",
        }
        st.markdown(f"""<div class="sss-card" style="border-top:4px solid {'#22B8CF' if has_bqms else '#3399CC'};text-align:center;">
            <div style="font-size:11px;opacity:0.5;letter-spacing:2px;">{branch['name'].upper()}</div>
            <div style="font-weight:700;margin:4px 0;">{t['category']} — {t['service']}</div>
            <span class="sss-badge" style="background:rgba(51,153,204,0.15);color:#3399CC;">
                {_slabels.get(t['status'], t['status'])}</span>
        </div>""", unsafe_allow_html=True)

        if has_bqms:
            st.markdown(f"""<div class="sss-card" style="text-align:center;">
                <div style="font-size:11px;opacity:0.5;">YOUR BQMS QUEUE NUMBER</div>
                <div class="sss-bqms">{t['bqmsNumber']}</div>
            </div>""", unsafe_allow_html=True)

            if not is_done and not is_ns:
                cat_obj = next((c for c in cats if c["id"] == t.get("categoryId")), None)
                bq      = fresh_bq.get(t.get("categoryId",""), {})
                ns_val  = bq.get("nowServing", "—")
                avg     = cat_obj["avgTime"] if cat_obj else 10
                ahead   = 0
                try:
                    ns_num = int("".join(filter(str.isdigit, str(ns_val))))
                    my_num = int("".join(filter(str.isdigit, str(t["bqmsNumber"]))))
                    ahead  = max(0, my_num - ns_num)
                except (ValueError, TypeError):
                    pass
                est = ahead * avg

                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f"""<div class="sss-metric">
                        <div class="val" style="color:#22B8CF;">{ns_val}</div>
                        <div class="lbl">Now Serving</div></div>""", unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""<div class="sss-metric">
                        <div class="val">{t['bqmsNumber']}</div>
                        <div class="lbl">Your #</div></div>""", unsafe_allow_html=True)
                with m3:
                    wait_txt = "Next!" if est == 0 else f"~{est}m"
                    st.markdown(f"""<div class="sss-metric">
                        <div class="val">{wait_txt}</div>
                        <div class="lbl">Est. Wait</div></div>""", unsafe_allow_html=True)
        else:
            if not is_done and not is_ns:
                st.markdown(f"""<div class="sss-card" style="text-align:center;">
                    <div style="font-size:11px;opacity:0.5;">RESERVATION NUMBER</div>
                    <div class="sss-resnum">{t['resNum']}</div>
                </div>""", unsafe_allow_html=True)
                st.markdown("""<div class="sss-alert sss-alert-yellow">
                    ⏳ <strong>Waiting for BQMS Number</strong><br/>
                    Staff will assign your number. This page auto-refreshes.
                </div>""", unsafe_allow_html=True)

        # Nav
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Refresh Now", use_container_width=True, type="primary"):
                st.rerun()
        with c2:
            if st.button("🔍 Track Another", use_container_width=True):
                st.session_state.tracked_id = None
                go("track_input")

        if not is_done and not is_ns:
            st.caption(f"🔄 Page auto-refreshes every 20s · "
                       f"Last: {now.strftime('%I:%M:%S %p')}")


# ═══════════════════════════════════════════════════
#  FOOTER + SYNC DIAGNOSTIC
# ═══════════════════════════════════════════════════
from shared_data import DATA_DIR
_qf = DATA_DIR / f"queue_{now.strftime('%Y-%m-%d')}.json"
st.markdown("---")
st.markdown(f"""<div style="text-align:center;font-size:10px;opacity:0.4;padding:8px;">
    RPT / SSS Gingoog Branch · MabiliSSS Queue {VER}<br/>
    🔗 Data: <code>{DATA_DIR}</code> · Q: <code>{_qf.name}</code>
    ({len(res)} entries) · Status: {o_stat}
    · Auto-refresh: {'✅' if _autorefresh_ok else '❌ NOT INSTALLED'}
</div>""", unsafe_allow_html=True)
