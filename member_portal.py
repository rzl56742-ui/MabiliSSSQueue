"""
═══════════════════════════════════════════════════════════════
 MabiliSSS Queue V1.0.0 — MEMBER PORTAL (Streamlit)
 Digital Priority Number Issuance System
 SSS Gingoog Branch — Reserve & Track Only
 Run: streamlit run member_portal.py --server.port 8501
 © RPT / SSS Gingoog Branch 2026
═══════════════════════════════════════════════════════════════
"""

import streamlit as st
from datetime import datetime, date
from shared_data import (
    VER, SSS_CSS, get_branch, get_categories, get_today_queue, save_today_queue,
    slot_counts, is_duplicate, gen_id, today_str, today_short, format_bqms_time,
    OSTATUS_MAP,
)

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="MabiliSSS Queue — Reserve",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(SSS_CSS, unsafe_allow_html=True)

# ── SESSION STATE INIT ──
for k, v in {
    "screen": "home", "sel_cat": None, "sel_svc": None, "pri_type": "regular",
    "ticket": None, "tracked_id": None, "consent": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── LOAD DATA (fresh every render / auto-refresh) ──
branch = get_branch()
cats = get_categories()
qdata = get_today_queue()
res = qdata.get("res", [])
bqms_state = qdata.get("bqmsState", {})
o_stat = qdata.get("oStat", "online")
is_open = o_stat != "offline"
sc = slot_counts(cats, res)
now = datetime.now()

def go(screen):
    st.session_state.screen = screen
    st.rerun()

# ═══════════════════════════════════════════════════
#  HEADER — always shown
# ═══════════════════════════════════════════════════
st.markdown(f"""<div class="sss-header">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div><h2>🏛️ MabiliSSS Queue</h2><p>{branch['name']} • {VER}</p></div>
        <div style="text-align:right;font-size:13px;opacity:0.8;">
            {now.strftime('%A, %B %d, %Y')}<br/>{now.strftime('%I:%M %p')}
        </div>
    </div>
</div>""", unsafe_allow_html=True)

# ── STATUS BAR ──
si = OSTATUS_MAP.get(o_stat, OSTATUS_MAP["online"])
st.markdown(f"""<div class="sss-alert sss-alert-{'green' if o_stat == 'online' else 'yellow' if o_stat == 'intermittent' else 'red'}"
    style="text-align:center;font-size:14px;">{si['label']}</div>""", unsafe_allow_html=True)

# ── ANNOUNCEMENT ──
if branch.get("announcement"):
    st.info(f"📢 {branch['announcement']}")

screen = st.session_state.screen

# ═══════════════════════════════════════════════════
#  HOME
# ═══════════════════════════════════════════════════
if screen == "home":
    # Stats
    active_q = len([r for r in res if r.get("status") not in ("COMPLETED", "NO_SHOW")])
    done_q = len([r for r in res if r.get("status") == "COMPLETED"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="sss-card sss-metric" style="background:#E6F2FA;">
            <div class="value" style="color:#0066A1;">{active_q}</div>
            <div class="label">Active Queue</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="sss-card sss-metric" style="background:#E8F8EF;">
            <div class="value" style="color:#0F9D58;">{done_q}</div>
            <div class="label">Served Today</div></div>""", unsafe_allow_html=True)

    # Action Buttons
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📋 **Reserve a Slot**", use_container_width=True, type="primary",
                      disabled=not is_open, help="Book your queue position online"):
            st.session_state.sel_cat = None
            st.session_state.sel_svc = None
            st.session_state.pri_type = "regular"
            st.session_state.consent = False
            go("select_cat")
    with c2:
        if st.button("🔍 **Track My Queue**", use_container_width=True,
                      help="Check live status & wait time"):
            st.session_state.tracked_id = None
            go("track_input")

    if not is_open:
        st.warning("⚠️ Reservation is currently closed. Please try again later or visit the branch.")

    # How It Works
    st.markdown("""<div class="sss-card" style="background:#FFF8E1; border-left: 4px solid #F7B928;">
        <strong>📌 Paano Gamitin (How It Works)</strong><br/><br/>
        1. Tap <b>"Reserve a Slot"</b> → fill in your details<br/>
        2. Go to the SSS branch during office hours<br/>
        3. Present reservation to guard / info desk<br/>
        4. Staff assigns your <b>official BQMS queue number</b><br/>
        5. Tap <b>"Track My Queue"</b> to monitor live!
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="sss-card"><strong>🔒 Privacy</strong><br/>
            <span style="font-size:12px;color:#5A7184;">RA 10173 compliant. Data for today only.</span></div>""",
            unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="sss-card"><strong>⏰ Schedule</strong><br/>
            <span style="font-size:12px;color:#5A7184;">{branch['hours']}<br/>BQMS: {format_bqms_time(branch.get('bqmsStartTime','08:00'))}</span></div>""",
            unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
#  SELECT CATEGORY
# ═══════════════════════════════════════════════════
elif screen == "select_cat":
    if st.button("← Back to Home"):
        go("home")
    st.subheader("Step 1: Choose Transaction")
    st.caption("What do you need today?")

    for cat in cats:
        s = sc.get(cat["id"], {"remaining": cat["cap"], "cap": cat["cap"]})
        full = s["remaining"] <= 0
        col1, col2 = st.columns([5, 1])
        with col1:
            btn_label = f"{cat['icon']} **{cat['label']}** — {len(cat.get('services',[]))} types"
            if st.button(btn_label, key=f"cat_{cat['id']}", disabled=full, use_container_width=True):
                st.session_state.sel_cat = cat["id"]
                go("select_svc")
        with col2:
            if full:
                st.markdown("<span style='color:red;font-weight:800;'>FULL</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:#0066A1;font-weight:800;font-size:18px;'>{s['remaining']}</span><br/><span style='font-size:10px;color:#94A7B8;'>left</span>", unsafe_allow_html=True)

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
            if st.button(f"● {svc['label']}", key=f"svc_{svc['id']}", use_container_width=True):
                st.session_state.sel_svc = svc["id"]
                go("member_form")

# ═══════════════════════════════════════════════════
#  MEMBER FORM
# ═══════════════════════════════════════════════════
elif screen == "member_form":
    cat = next((c for c in cats if c["id"] == st.session_state.sel_cat), None)
    svc = None
    if cat:
        svc = next((s for s in cat.get("services", []) if s["id"] == st.session_state.sel_svc), None)
    if not cat or not svc:
        go("select_cat")
    else:
        if st.button("← Back"):
            go("select_svc")
        st.subheader("Step 3: Your Details")
        st.markdown(f"""<div class="sss-card">{cat['icon']} <strong>{svc['label']}</strong><br/>
            <span style="color:#5A7184;">{cat['label']}</span></div>""", unsafe_allow_html=True)

        with st.form("reserve_form"):
            st.markdown("**👤 Member Information**")
            c1, c2 = st.columns(2)
            with c1:
                last_name = st.text_input("Last Name *", placeholder="e.g., DELA CRUZ").upper()
            with c2:
                first_name = st.text_input("First Name *", placeholder="e.g., JUAN").upper()
            c1, c2 = st.columns([1, 3])
            with c1:
                mi = st.text_input("M.I.", max_chars=2, placeholder="M").upper()
            with c2:
                mobile = st.text_input("Mobile Number *", placeholder="09XX XXX XXXX")

            st.markdown("---")
            st.markdown("**Queue Lane**")
            pri = st.radio("Select lane:", ["👤 Regular", "⭐ Priority (Senior/PWD/Pregnant)"],
                           horizontal=True, index=0)
            pri_type = "priority" if "Priority" in pri else "regular"

            if pri_type == "priority":
                st.error("⚠️ **Senior 60+, PWD, Pregnant, Solo Parent ONLY.** Non-qualifiers → END OF REGULAR LINE.")

            st.markdown("---")
            st.markdown("**🔒 Data Privacy Consent (RA 10173)**")
            st.caption(f"Your name and mobile number are collected solely for today's queue management at {branch['name']}. Data will not be shared or retained beyond the business day.")
            consent = st.checkbox("I consent to the collection and use of my data as described.")

            submitted = st.form_submit_button("📋 Reserve My Slot", type="primary", use_container_width=True)

            if submitted:
                # Re-read fresh data
                fresh = get_today_queue()
                fresh_res = fresh.get("res", [])
                fresh_sc = slot_counts(cats, fresh_res)

                errors = []
                if not last_name.strip():
                    errors.append("Last Name is required.")
                if not first_name.strip():
                    errors.append("First Name is required.")
                if not mobile.strip() or len(mobile.strip()) < 10:
                    errors.append("Valid mobile number required (min 10 digits).")
                if not consent:
                    errors.append("Check the data privacy consent.")
                s = fresh_sc.get(cat["id"], {"remaining": 0})
                if s["remaining"] <= 0:
                    errors.append(f"Slots full for {cat['label']}.")
                if is_duplicate(fresh_res, last_name, first_name, mobile):
                    errors.append("You already have an active reservation today.")

                if errors:
                    for e in errors:
                        st.error(f"❌ {e}")
                else:
                    slot_num = s["used"] + 1 if "used" in s else len(fresh_res) + 1
                    res_num = f"R-{today_short()}-{slot_num:03d}"
                    entry = {
                        "id": gen_id(), "slot": slot_num, "resNum": res_num,
                        "lastName": last_name.strip(), "firstName": first_name.strip(),
                        "mi": mi.strip(), "mobile": mobile.strip(),
                        "service": svc["label"], "serviceId": svc["id"],
                        "category": cat["label"], "categoryId": cat["id"],
                        "catIcon": cat["icon"], "priority": pri_type,
                        "status": "RESERVED", "bqmsNumber": None,
                        "source": "ONLINE", "issuedAt": datetime.now().isoformat(),
                        "arrivedAt": None, "completedAt": None,
                    }
                    fresh_res.append(entry)
                    fresh["res"] = fresh_res
                    save_today_queue(fresh)
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
        st.markdown("""<div style="text-align:center;margin:10px 0;">
            <span style="font-size:48px;">✅</span>
            <h2 style="color:#0F9D58;margin:4px 0;">Slot Reserved!</h2></div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="sss-card" style="border-top:4px solid #0066A1; text-align:center;">
            <div style="font-size:11px;color:#94A7B8;letter-spacing:2px;">MABILISSS QUEUE — {branch['name'].upper()}</div>
            <div style="font-weight:700;margin:4px 0;">{t['category']} — {t['service']}</div>
            <hr style="border:1px dashed #D6E4EE;"/>
            <div style="font-size:11px;color:#94A7B8;">RESERVATION NUMBER</div>
            <div class="sss-resnum">{t['resNum']}</div>
            <hr style="border:1px dashed #D6E4EE;"/>
            <table style="width:100%;font-size:13px;">
                <tr><td style="color:#5A7184;text-align:left;">Name</td><td style="text-align:right;font-weight:700;">{t['lastName']}, {t['firstName']} {t['mi']}</td></tr>
                <tr><td style="color:#5A7184;text-align:left;">Mobile</td><td style="text-align:right;font-weight:700;">{t['mobile']}</td></tr>
                <tr><td style="color:#5A7184;text-align:left;">Lane</td><td style="text-align:right;font-weight:700;">{'⭐ Priority' if t['priority'] == 'priority' else '👤 Regular'}</td></tr>
            </table></div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="sss-card" style="background:#E6F2FA;">
            <strong>📋 Next Steps:</strong><br/><br/>
            1. Save: <code style="font-size:16px;font-weight:900;">{t['resNum']}</code><br/>
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
            if st.button("🔍 Track Now →", use_container_width=True, type="primary"):
                st.session_state.tracked_id = t["id"]
                go("tracker")

# ═══════════════════════════════════════════════════
#  TRACK INPUT
# ═══════════════════════════════════════════════════
elif screen == "track_input":
    if st.button("← Back to Home"):
        go("home")

    st.markdown("""<div style="text-align:center;margin:10px 0;">
        <span style="font-size:36px;">🔍</span>
        <h3>Track Your Queue</h3>
        <p style="color:#5A7184;">See your live BQMS number and wait time.</p></div>""", unsafe_allow_html=True)

    track_mode = st.radio("Search by:", ["📱 Mobile Number", "#️⃣ Reservation Number"], horizontal=True)

    with st.form("track_form"):
        if "Mobile" in track_mode:
            track_val = st.text_input("Enter your mobile number", placeholder="09XX XXX XXXX")
        else:
            track_val = st.text_input("Enter reservation number", placeholder="e.g., R-0214-005").upper()

        if st.form_submit_button("🔍 Find My Queue", type="primary", use_container_width=True):
            fresh = get_today_queue()
            fresh_res = fresh.get("res", [])
            v = track_val.strip()
            if not v:
                st.error("Please enter your mobile number or reservation number.")
            else:
                found = None
                if "Mobile" in track_mode:
                    for r in fresh_res:
                        if r.get("mobile") == v and r.get("status") not in ("COMPLETED", "NO_SHOW"):
                            found = r; break
                    if not found:
                        for r in fresh_res:
                            if r.get("mobile") == v:
                                found = r; break
                else:
                    vu = v.upper()
                    for r in fresh_res:
                        if r.get("resNum") == vu and r.get("status") not in ("COMPLETED", "NO_SHOW"):
                            found = r; break
                    if not found:
                        for r in fresh_res:
                            if r.get("resNum") == vu:
                                found = r; break

                if not found:
                    st.error("❌ Not found. Check your input and try again.")
                else:
                    st.session_state.tracked_id = found["id"]
                    go("tracker")

# ═══════════════════════════════════════════════════
#  LIVE TRACKER
# ═══════════════════════════════════════════════════
elif screen == "tracker":
    tid = st.session_state.tracked_id
    # Fresh read
    fresh = get_today_queue()
    fresh_res = fresh.get("res", [])
    fresh_bqms = fresh.get("bqmsState", {})

    t = next((r for r in fresh_res if r.get("id") == tid), None)
    if not t:
        st.error("❌ Entry not found.")
        if st.button("← Try Again"):
            go("track_input")
    else:
        has_bqms = bool(t.get("bqmsNumber"))
        is_done = t.get("status") == "COMPLETED"
        is_ns = t.get("status") == "NO_SHOW"
        is_serving = t.get("status") == "SERVING"

        # Status alerts
        if is_serving:
            st.markdown("""<div class="sss-alert sss-alert-blue" style="text-align:center;font-size:18px;">
                🎉 <strong>YOU'RE BEING SERVED!</strong><br/>Proceed to the counter now.</div>""", unsafe_allow_html=True)
        elif is_done:
            st.markdown(f"""<div class="sss-alert sss-alert-green" style="text-align:center;">
                ✅ <strong>Completed</strong><br/>Thank you for visiting {branch['name']}!</div>""", unsafe_allow_html=True)
        elif is_ns:
            st.markdown("""<div class="sss-alert sss-alert-red" style="text-align:center;">
                ❌ <strong>No-Show</strong><br/>Please create a new reservation.</div>""", unsafe_allow_html=True)

        # Main card
        status_labels = {"RESERVED":"📋 RESERVED","ARRIVED":"✅ ARRIVED","SERVING":"🔵 NOW SERVING","COMPLETED":"✅ DONE","NO_SHOW":"❌ NO-SHOW"}
        st.markdown(f"""<div class="sss-card" style="border-top:4px solid {'#0891B2' if has_bqms else '#0066A1'};text-align:center;">
            <div style="font-size:11px;color:#94A7B8;letter-spacing:2px;">{branch['name'].upper()}</div>
            <div style="font-weight:700;margin:4px 0;">{t['category']} — {t['service']}</div>
            <div><span class="sss-badge" style="background:#E6F2FA;color:#0066A1;">{status_labels.get(t['status'], t['status'])}</span></div>
        </div>""", unsafe_allow_html=True)

        if has_bqms:
            st.markdown(f"""<div class="sss-card" style="text-align:center;">
                <div style="font-size:11px;color:#94A7B8;">YOUR BQMS QUEUE NUMBER</div>
                <div class="sss-bqms">{t['bqmsNumber']}</div></div>""", unsafe_allow_html=True)

            if not is_done and not is_ns:
                # Wait estimate
                cat = next((c for c in cats if c["id"] == t.get("categoryId")), None)
                bq = fresh_bqms.get(t.get("categoryId", ""), {})
                now_serving = bq.get("nowServing", "—")
                avg = cat["avgTime"] if cat else 10
                ahead = 0
                try:
                    ns_num = int("".join(filter(str.isdigit, str(now_serving))))
                    my_num = int("".join(filter(str.isdigit, str(t["bqmsNumber"]))))
                    ahead = max(0, my_num - ns_num)
                except (ValueError, TypeError):
                    pass
                est = ahead * avg

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"""<div class="sss-metric"><div class="value" style="color:#0891B2;">{now_serving}</div>
                        <div class="label">Now Serving</div></div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div class="sss-metric"><div class="value">{t['bqmsNumber']}</div>
                        <div class="label">Your #</div></div>""", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""<div class="sss-metric"><div class="value">{'Next!' if est == 0 else f'~{est}m'}</div>
                        <div class="label">Wait</div></div>""", unsafe_allow_html=True)
        else:
            if not is_done and not is_ns:
                st.markdown(f"""<div class="sss-card" style="text-align:center;">
                    <div style="font-size:11px;color:#94A7B8;">RESERVATION NUMBER</div>
                    <div class="sss-resnum">{t['resNum']}</div></div>""", unsafe_allow_html=True)
                st.markdown("""<div class="sss-alert sss-alert-yellow" style="text-align:center;">
                    ⏳ <strong>Waiting for BQMS Number</strong><br/>
                    Staff will assign your number. Click Refresh to check.</div>""", unsafe_allow_html=True)

        # Refresh + Nav
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Refresh", use_container_width=True, type="primary"):
                st.rerun()
        with c2:
            if st.button("🔍 Track Another", use_container_width=True):
                st.session_state.tracked_id = None
                go("track_input")

        if not is_done and not is_ns:
            st.caption(f"💡 Click **Refresh** to check for updates. Last checked: {now.strftime('%I:%M:%S %p')}")

# ── FOOTER ──
st.markdown(f"""<div style="text-align:center;margin-top:40px;font-size:10px;color:#94A7B8;opacity:0.5;">
    RPT / SSS Gingoog Branch • MabiliSSS Queue {VER}</div>""", unsafe_allow_html=True)
