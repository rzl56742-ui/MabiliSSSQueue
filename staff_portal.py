"""
═══════════════════════════════════════════════════════════════
 MabiliSSS Queue V1.0.0 — STAFF PORTAL (Streamlit)
 Digital Priority Number Issuance System
 SSS Gingoog Branch — Authorized Personnel Only
 Run: streamlit run staff_portal.py --server.port 8502
 © RPT / SSS Gingoog Branch 2026
═══════════════════════════════════════════════════════════════
"""

import streamlit as st
import time as _time
from datetime import datetime, date
from shared_data import (
    VER, SSS_CSS, ROLE_META, OSTATUS_MAP,
    get_branch, save_branch, get_categories, save_categories,
    get_users, save_users, get_today_queue, save_today_queue,
    slot_counts, is_duplicate, gen_id, today_str, today_short,
    get_queue_csv, list_queue_days, DEF_USERS,
)

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="MabiliSSS Queue — Staff",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(SSS_CSS, unsafe_allow_html=True)

# ── SESSION INIT ──
for k, v in {
    "auth_user": None, "fail_count": 0, "lock_until": 0,
    "staff_tab": "queue", "admin_tab": "users", "dash_tab": "overview",
    "queue_filter": "UNASSIGNED", "assign_id": None, "last_activity": _time.time(),
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

now = datetime.now()

# ── SESSION TIMEOUT (30 min) ──
if st.session_state.auth_user and (_time.time() - st.session_state.last_activity > 30 * 60):
    st.session_state.auth_user = None
    st.warning("Session expired. Please log in again.")

def touch():
    st.session_state.last_activity = _time.time()

# ═══════════════════════════════════════════════════
#  LOGIN SCREEN
# ═══════════════════════════════════════════════════
if not st.session_state.auth_user:
    st.markdown("""<div class="sss-header" style="text-align:center;">
        <span style="font-size:36px;">🔐</span>
        <h2>MabiliSSS Queue</h2>
        <p>Staff Portal — Authorized Personnel Only</p>
    </div>""", unsafe_allow_html=True)

    locked = _time.time() < st.session_state.lock_until
    if locked:
        remaining = int(st.session_state.lock_until - _time.time())
        st.error(f"🔒 Account locked. Try again in {remaining} seconds.")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="e.g., staff1, kiosk, th, bh")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True, disabled=locked)

        if submitted and not locked:
            users = get_users()
            u = next((x for x in users if x["username"].lower() == username.strip().lower() and x.get("active", True)), None)
            if not u:
                st.error("❌ User not found or account inactive.")
            elif u["password"] != password:
                st.session_state.fail_count += 1
                left = 3 - st.session_state.fail_count
                if left <= 0:
                    st.session_state.lock_until = _time.time() + 300
                    st.session_state.fail_count = 0
                    st.error("❌ 3 failed attempts. Locked for 5 minutes.")
                else:
                    st.error(f"❌ Wrong password. {left} attempt(s) left.")
            else:
                st.session_state.auth_user = u
                st.session_state.fail_count = 0
                st.session_state.staff_tab = "queue"
                st.session_state.queue_filter = "UNASSIGNED"
                touch()
                st.rerun()

    st.caption("Default password: **mnd2026** • Contact TH/SH for password reset.")
    st.markdown(f"<div style='text-align:center;font-size:10px;color:#94A7B8;margin-top:20px;'>{VER}</div>", unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════
#  AUTHENTICATED — Load data
# ═══════════════════════════════════════════════════
touch()
user = st.session_state.auth_user
role = user["role"]
branch = get_branch()
cats = get_categories()
users = get_users()
qdata = get_today_queue()
res = qdata.get("res", [])
bqms_state = qdata.get("bqmsState", {})
o_stat = qdata.get("oStat", "online")
sc = slot_counts(cats, res)

rm = ROLE_META.get(role, {})

# ── HEADER ──
st.markdown(f"""<div class="sss-header" style="background:linear-gradient(135deg,#002E52,#004D7A);">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div><h2>{rm.get('icon','')} MabiliSSS Staff</h2>
            <p>{user['displayName']} • {rm.get('label',role)}</p></div>
        <div style="text-align:right;font-size:12px;opacity:0.8;">{now.strftime('%I:%M %p')}<br/>{today_str()}</div>
    </div>
</div>""", unsafe_allow_html=True)

# ── TOP NAV ──
nav_cols = st.columns([1,1,1,1,1])
with nav_cols[0]:
    if st.button("📋 Queue", use_container_width=True, type="primary" if st.session_state.staff_tab == "queue" else "secondary"):
        st.session_state.staff_tab = "queue"; st.rerun()
if role in ("th",):
    with nav_cols[1]:
        if st.button("👔 Admin", use_container_width=True, type="primary" if st.session_state.staff_tab == "admin" else "secondary"):
            st.session_state.staff_tab = "admin"; st.rerun()
if role in ("th", "bh", "dh"):
    with nav_cols[2]:
        if st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state.staff_tab == "dash" else "secondary"):
            st.session_state.staff_tab = "dash"; st.rerun()
with nav_cols[3]:
    if st.button("🔑 Password", use_container_width=True):
        st.session_state.staff_tab = "change_pw"; st.rerun()
with nav_cols[4]:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.auth_user = None; st.rerun()

tab = st.session_state.staff_tab
is_readonly = role in ("bh", "dh")

# ═══════════════════════════════════════════════════
#  CHANGE PASSWORD
# ═══════════════════════════════════════════════════
if tab == "change_pw":
    st.subheader("🔑 Change Password")
    with st.form("pw_form"):
        new_pw = st.text_input("New Password", type="password", help="Min 4 characters")
        new_pw2 = st.text_input("Confirm Password", type="password")
        if st.form_submit_button("Save Password", type="primary"):
            if len(new_pw) < 4:
                st.error("Min 4 characters.")
            elif new_pw != new_pw2:
                st.error("Passwords don't match.")
            else:
                all_users = get_users()
                for u in all_users:
                    if u["id"] == user["id"]:
                        u["password"] = new_pw
                save_users(all_users)
                st.session_state.auth_user["password"] = new_pw
                st.success("✅ Password changed!")
                st.session_state.staff_tab = "queue"
                st.rerun()

# ═══════════════════════════════════════════════════
#  QUEUE CONSOLE
# ═══════════════════════════════════════════════════
elif tab == "queue":
    unassigned = [r for r in res if not r.get("bqmsNumber") and r.get("status") not in ("NO_SHOW", "COMPLETED")]

    if not is_readonly:
        # STATUS TOGGLE
        st.markdown("**System Status**")
        status_options = ["🟢 Online", "🟡 Intermittent", "🔴 Offline"]
        status_map = {"🟢 Online": "online", "🟡 Intermittent": "intermittent", "🔴 Offline": "offline"}
        reverse_map = {"online": "🟢 Online", "intermittent": "🟡 Intermittent", "offline": "🔴 Offline"}
        new_stat = st.radio("Reservation status:", status_options, horizontal=True,
                            index=status_options.index(reverse_map.get(o_stat, "🟢 Online")))
        if status_map[new_stat] != o_stat:
            qdata["oStat"] = status_map[new_stat]
            save_today_queue(qdata)
            st.rerun()

        # UNASSIGNED ALERT
        if unassigned:
            st.markdown(f"""<div class="sss-alert sss-alert-red" style="font-size:16px;">
                🔴 <strong>{len(unassigned)} NEED BQMS#</strong> — Assign numbers below ↓</div>""", unsafe_allow_html=True)

        # BQMS NOW SERVING
        with st.expander("🔄 BQMS — Now Serving (click to update)", expanded=False):
            with st.form("bqms_form"):
                cols_per_row = 2
                changed = False
                new_bqms = dict(bqms_state)
                cat_pairs = [(cats[i], cats[i+1] if i+1 < len(cats) else None) for i in range(0, len(cats), 2)]
                for c1_cat, c2_cat in cat_pairs:
                    col1, col2 = st.columns(2)
                    with col1:
                        cur = bqms_state.get(c1_cat["id"], {}).get("nowServing", "")
                        val = st.text_input(f"{c1_cat['icon']} {c1_cat['short']}", value=cur, key=f"bqms_{c1_cat['id']}")
                        if val != cur:
                            new_bqms[c1_cat["id"]] = {"nowServing": val.upper()}
                    if c2_cat:
                        with col2:
                            cur2 = bqms_state.get(c2_cat["id"], {}).get("nowServing", "")
                            val2 = st.text_input(f"{c2_cat['icon']} {c2_cat['short']}", value=cur2, key=f"bqms_{c2_cat['id']}")
                            if val2 != cur2:
                                new_bqms[c2_cat["id"]] = {"nowServing": val2.upper()}
                if st.form_submit_button("Update Now Serving", type="primary", use_container_width=True):
                    qdata["bqmsState"] = new_bqms
                    save_today_queue(qdata)
                    st.success("✅ Updated!")
                    st.rerun()

        # WALK-IN
        with st.expander("➕ Add Walk-in Member", expanded=False):
            with st.form("walkin_form"):
                w_cat_opts = {f"{c['icon']} {c['label']} ({sc.get(c['id'],{}).get('remaining',0)} left)": c["id"] for c in cats}
                w_cat_sel = st.selectbox("Category *", ["— Select —"] + list(w_cat_opts.keys()))
                w_cat_id = w_cat_opts.get(w_cat_sel, "")
                w_cat_obj = next((c for c in cats if c["id"] == w_cat_id), None)

                w_svc_id = ""
                if w_cat_obj:
                    svc_opts = {"— None —": ""} | {s["label"]: s["id"] for s in w_cat_obj.get("services", [])}
                    w_svc_sel = st.selectbox("Sub-service (optional)", list(svc_opts.keys()))
                    w_svc_id = svc_opts.get(w_svc_sel, "")

                wc1, wc2 = st.columns(2)
                with wc1: w_last = st.text_input("Last Name *", key="wl").upper()
                with wc2: w_first = st.text_input("First Name *", key="wf").upper()
                wc1, wc2 = st.columns([1,3])
                with wc1: w_mi = st.text_input("M.I.", max_chars=2, key="wmi").upper()
                with wc2: w_mob = st.text_input("Mobile", key="wmob", placeholder="Optional")
                w_pri = st.radio("Lane:", ["👤 Regular", "⭐ Priority"], horizontal=True, key="wpri")
                w_bqms = ""
                if role != "kiosk":
                    w_bqms = st.text_input("BQMS # (if already issued)", key="wbqms", placeholder="Leave blank if not yet").upper()

                if st.form_submit_button("Register Walk-in ✓", type="primary", use_container_width=True):
                    if not w_cat_id or not w_last.strip() or not w_first.strip():
                        st.error("Category, Last Name, First Name required.")
                    elif is_duplicate(res, w_last, w_first, w_mob):
                        st.error("Duplicate: active reservation exists.")
                    else:
                        fresh = get_today_queue()
                        fresh_res = fresh.get("res", [])
                        s = slot_counts(cats, fresh_res).get(w_cat_id, {"used": 0, "cap": 50})
                        if s["used"] >= s["cap"]:
                            st.error(f"Cap reached for this category.")
                        else:
                            slot = s["used"] + 1
                            rn = f"K-{today_short()}-{slot:03d}"
                            svc_obj = next((sv for sv in (w_cat_obj or {}).get("services",[]) if sv["id"] == w_svc_id), None)
                            entry = {
                                "id": gen_id(), "slot": slot, "resNum": rn,
                                "lastName": w_last.strip(), "firstName": w_first.strip(),
                                "mi": w_mi.strip(), "mobile": w_mob.strip(),
                                "service": svc_obj["label"] if svc_obj else "Walk-in",
                                "serviceId": w_svc_id or "walkin",
                                "category": w_cat_obj["label"], "categoryId": w_cat_id,
                                "catIcon": w_cat_obj["icon"],
                                "priority": "priority" if "Priority" in w_pri else "regular",
                                "status": "ARRIVED" if w_bqms.strip() else "RESERVED",
                                "bqmsNumber": w_bqms.strip() if w_bqms.strip() else None,
                                "source": "KIOSK", "issuedAt": datetime.now().isoformat(),
                                "arrivedAt": datetime.now().isoformat() if w_bqms.strip() else None,
                                "completedAt": None,
                            }
                            fresh_res.append(entry)
                            fresh["res"] = fresh_res
                            save_today_queue(fresh)
                            st.success(f"✅ Registered: {rn}")
                            st.rerun()

    # ── FILTERS ──
    st.markdown("---")
    filter_opts = {
        "🔴 Need BQMS": "UNASSIGNED", "All": "all", "🏢 Kiosk": "KIOSK", "📱 Online": "ONLINE",
        "✅ Arrived": "ARRIVED", "✔ Done": "COMPLETED", "❌ No-Show": "NO_SHOW"
    }
    sel_filter = st.radio("Filter:", list(filter_opts.keys()), horizontal=True, index=0)
    qf = filter_opts[sel_filter]

    search = st.text_input("🔍 Search by name, BQMS#, or Res#", key="qsearch")

    # ── FILTER LOGIC ──
    sorted_res = sorted(res, key=lambda r: (0 if r.get("source") == "KIOSK" else 1, r.get("issuedAt", "")))
    filtered = sorted_res
    if qf == "UNASSIGNED":
        filtered = [r for r in filtered if not r.get("bqmsNumber") and r.get("status") not in ("NO_SHOW","COMPLETED")]
    elif qf == "KIOSK":
        filtered = [r for r in filtered if r.get("source") == "KIOSK"]
    elif qf == "ONLINE":
        filtered = [r for r in filtered if r.get("source") == "ONLINE"]
    elif qf != "all":
        filtered = [r for r in filtered if r.get("status") == qf]
    if search:
        s = search.lower()
        filtered = [r for r in filtered if s in r.get("lastName","").lower() or s in r.get("firstName","").lower()
                    or s in (r.get("bqmsNumber","") or "").lower() or s in (r.get("resNum","") or "").lower()]

    st.caption(f"Showing {len(filtered)} entries")

    if not filtered:
        if qf == "UNASSIGNED":
            st.success("✅ All entries have been assigned BQMS numbers!")
        else:
            st.info("No entries match this filter.")
    else:
        for r in filtered:
            needs_bqms = not r.get("bqmsNumber") and r.get("status") not in ("NO_SHOW", "COMPLETED")
            border_color = "#DC3545" if needs_bqms else "#D6E4EE"
            src_icon = "🏢" if r.get("source") == "KIOSK" else "📱"
            pri_icon = "⭐" if r.get("priority") == "priority" else "👤"
            status_labels = {"RESERVED":"📋 RES","ARRIVED":"✅ ARR","SERVING":"🔵 SRV","COMPLETED":"✅ DONE","NO_SHOW":"❌ NS"}

            st.markdown(f"""<div class="sss-card" style="border-left:4px solid {border_color};">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <strong>{r.get('catIcon','')} {r['lastName']}, {r['firstName']} {r.get('mi','')}</strong><br/>
                        <span style="font-size:11px;color:#5A7184;">{r.get('service','')} • {pri_icon} • {r.get('resNum','')}</span>
                    </div>
                    <div style="text-align:right;">
                        <span class="sss-badge" style="background:#E6F2FA;color:#0066A1;">{status_labels.get(r['status'], r['status'])}</span>
                        <span class="sss-badge" style="background:{'#FFF8E1' if r.get('source')=='KIOSK' else '#E0F7FA'};color:{'#7A5D00' if r.get('source')=='KIOSK' else '#0E7490'};">{src_icon}</span>
                        {'<div style="font-family:monospace;font-size:18px;font-weight:900;color:#0891B2;margin-top:4px;">'+r['bqmsNumber']+'</div>' if r.get('bqmsNumber') else ''}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # ── ACTION BUTTONS ──
            if not is_readonly:
                if needs_bqms:
                    ac1, ac2 = st.columns([3, 1])
                    with ac1:
                        bqms_val = st.text_input("BQMS#", key=f"assign_{r['id']}", placeholder="e.g., L-023", label_visibility="collapsed")
                    with ac2:
                        if st.button("🎫 Assign", key=f"btn_assign_{r['id']}", type="primary", use_container_width=True):
                            if bqms_val.strip():
                                fresh = get_today_queue()
                                for fr in fresh["res"]:
                                    if fr["id"] == r["id"]:
                                        fr["bqmsNumber"] = bqms_val.strip().upper()
                                        fr["status"] = "ARRIVED"
                                        fr["arrivedAt"] = datetime.now().isoformat()
                                save_today_queue(fresh)
                                st.rerun()
                            else:
                                st.warning("Enter a BQMS number first.")
                    # No-Show button for unassigned
                    if st.button(f"❌ No-Show", key=f"ns_{r['id']}", use_container_width=True):
                        fresh = get_today_queue()
                        for fr in fresh["res"]:
                            if fr["id"] == r["id"]:
                                fr["status"] = "NO_SHOW"
                        save_today_queue(fresh)
                        st.rerun()

                elif r.get("status") == "ARRIVED":
                    ac1, ac2, ac3 = st.columns(3)
                    with ac1:
                        if st.button("🔵 Serving", key=f"srv_{r['id']}", use_container_width=True):
                            fresh = get_today_queue()
                            for fr in fresh["res"]:
                                if fr["id"] == r["id"]: fr["status"] = "SERVING"
                            save_today_queue(fresh); st.rerun()
                    with ac2:
                        if st.button("✅ Complete", key=f"done_{r['id']}", use_container_width=True):
                            fresh = get_today_queue()
                            for fr in fresh["res"]:
                                if fr["id"] == r["id"]:
                                    fr["status"] = "COMPLETED"; fr["completedAt"] = datetime.now().isoformat()
                            save_today_queue(fresh); st.rerun()
                    with ac3:
                        if st.button("❌ NS", key=f"ns2_{r['id']}", use_container_width=True):
                            fresh = get_today_queue()
                            for fr in fresh["res"]:
                                if fr["id"] == r["id"]: fr["status"] = "NO_SHOW"
                            save_today_queue(fresh); st.rerun()

                elif r.get("status") == "SERVING":
                    if st.button("✅ Complete", key=f"done2_{r['id']}", type="primary", use_container_width=True):
                        fresh = get_today_queue()
                        for fr in fresh["res"]:
                            if fr["id"] == r["id"]:
                                fr["status"] = "COMPLETED"; fr["completedAt"] = datetime.now().isoformat()
                        save_today_queue(fresh); st.rerun()

            st.markdown("")  # spacer

    # Refresh
    st.markdown("---")
    if st.button("🔄 Refresh Queue", use_container_width=True):
        st.rerun()

# ═══════════════════════════════════════════════════
#  ADMIN PANEL (TH only)
# ═══════════════════════════════════════════════════
elif tab == "admin" and role == "th":
    st.subheader("👔 Admin Panel")
    admin_tabs = st.tabs(["👥 Users", "📋 Categories", "🔢 Caps", "🏛️ Branch", "📢 Announcement"])

    # ── USERS ──
    with admin_tabs[0]:
        st.markdown("**Staff Accounts** — Edit names, reset passwords, add/deactivate staff.")
        st.caption("Default password: **mnd2026**")

        all_users = get_users()
        for u in all_users:
            rm_u = ROLE_META.get(u["role"], {})
            active_badge = "🟢" if u.get("active", True) else "🔴 inactive"
            st.markdown(f"""<div class="sss-card">
                <strong>{rm_u.get('icon','')} {u['displayName']}</strong> {active_badge}<br/>
                <span style="font-size:11px;color:#5A7184;">@{u['username']} • {rm_u.get('label', u['role'])}</span>
            </div>""", unsafe_allow_html=True)

            uc1, uc2, uc3, uc4 = st.columns(4)
            with uc1:
                new_name = st.text_input("Name", value=u["displayName"], key=f"uname_{u['id']}", label_visibility="collapsed")
                if new_name != u["displayName"]:
                    if st.button("💾 Save", key=f"savename_{u['id']}"):
                        for x in all_users:
                            if x["id"] == u["id"]: x["displayName"] = new_name.strip()
                        save_users(all_users)
                        st.success(f"✅ Name updated to {new_name}")
                        st.rerun()
            with uc2:
                new_role = st.selectbox("Role", list(ROLE_META.keys()),
                                        index=list(ROLE_META.keys()).index(u["role"]),
                                        key=f"urole_{u['id']}", label_visibility="collapsed",
                                        format_func=lambda x: f"{ROLE_META[x]['icon']} {ROLE_META[x]['label']}")
                if new_role != u["role"]:
                    if st.button("💾", key=f"saverole_{u['id']}"):
                        for x in all_users:
                            if x["id"] == u["id"]: x["role"] = new_role
                        save_users(all_users)
                        st.success("✅ Role updated"); st.rerun()
            with uc3:
                if st.button("🔑 Reset PW", key=f"rpw_{u['id']}"):
                    for x in all_users:
                        if x["id"] == u["id"]: x["password"] = "mnd2026"
                    save_users(all_users)
                    st.success(f"✅ Password reset to mnd2026")
            with uc4:
                active = u.get("active", True)
                if st.button("🔴 Off" if active else "🟢 On", key=f"tog_{u['id']}"):
                    for x in all_users:
                        if x["id"] == u["id"]: x["active"] = not active
                    save_users(all_users)
                    st.rerun()

        st.markdown("---")
        st.markdown("**+ Add New Staff User**")
        with st.form("add_user_form"):
            nu_user = st.text_input("Username", placeholder="e.g., staff3")
            nu_name = st.text_input("Display Name", placeholder="e.g., Juan Dela Cruz")
            nu_role = st.selectbox("Role", list(ROLE_META.keys()),
                                   format_func=lambda x: f"{ROLE_META[x]['icon']} {ROLE_META[x]['label']}")
            if st.form_submit_button("Add User", type="primary"):
                if not nu_user.strip() or not nu_name.strip():
                    st.error("Username and Display Name required.")
                elif any(x["username"].lower() == nu_user.strip().lower() for x in all_users):
                    st.error("Username already exists.")
                else:
                    all_users.append({
                        "id": gen_id(), "username": nu_user.strip().lower(),
                        "displayName": nu_name.strip(), "role": nu_role,
                        "password": "mnd2026", "active": True,
                    })
                    save_users(all_users)
                    st.success(f"✅ Added {nu_name} (@{nu_user})")
                    st.rerun()

    # ── CATEGORIES ──
    with admin_tabs[1]:
        st.markdown("**Service Categories**")
        for i, cat in enumerate(cats):
            with st.expander(f"{cat['icon']} {cat['label']} — {len(cat.get('services',[]))} subs"):
                with st.form(f"cat_edit_{i}"):
                    c1, c2 = st.columns(2)
                    with c1: new_label = st.text_input("Label", value=cat["label"], key=f"cl_{i}")
                    with c2: new_icon = st.text_input("Icon", value=cat["icon"], key=f"ci_{i}")
                    c1, c2, c3 = st.columns(3)
                    with c1: new_short = st.text_input("Short", value=cat["short"], key=f"cs_{i}")
                    with c2: new_avg = st.number_input("Avg Time (min)", value=cat["avgTime"], key=f"ca_{i}")
                    with c3: new_cap = st.number_input("Cap", value=cat["cap"], key=f"cc_{i}")

                    st.markdown("**Sub-transactions:**")
                    svc_text = "\n".join([s["label"] for s in cat.get("services", [])])
                    new_svcs_raw = st.text_area("One per line:", value=svc_text, key=f"csvcs_{i}")

                    if st.form_submit_button("Save Category"):
                        new_svcs = []
                        for line in new_svcs_raw.strip().split("\n"):
                            if line.strip():
                                sid = line.strip().lower().replace(" ", "_").replace("/", "_")[:20]
                                new_svcs.append({"id": sid, "label": line.strip()})
                        cats[i] = {**cat, "label": new_label, "icon": new_icon, "short": new_short,
                                   "avgTime": int(new_avg), "cap": int(new_cap), "services": new_svcs}
                        save_categories(cats)
                        st.success("✅ Saved!"); st.rerun()

    # ── CAPS ──
    with admin_tabs[2]:
        st.markdown("**Daily Slot Caps**")
        with st.form("caps_form"):
            new_caps = {}
            for cat in cats:
                s = sc.get(cat["id"], {"used": 0})
                new_caps[cat["id"]] = st.number_input(
                    f"{cat['icon']} {cat['short']} (used: {s['used']})",
                    value=cat["cap"], min_value=1, key=f"cap_{cat['id']}")
            if st.form_submit_button("Save Caps", type="primary"):
                for cat in cats:
                    cat["cap"] = new_caps[cat["id"]]
                save_categories(cats)
                st.success("✅ Caps updated!"); st.rerun()

    # ── BRANCH ──
    with admin_tabs[3]:
        with st.form("branch_form"):
            b_name = st.text_input("Branch Name", value=branch["name"])
            b_addr = st.text_input("Address", value=branch["address"])
            b_hours = st.text_input("Hours", value=branch["hours"])
            b_phone = st.text_input("Phone", value=branch.get("phone", ""))
            c1, c2, c3 = st.columns(3)
            with c1: b_open = st.text_input("Res. Open", value=branch.get("openTime", "06:00"))
            with c2: b_close = st.text_input("Res. Close", value=branch.get("closeTime", "16:00"))
            with c3: b_bqms = st.text_input("BQMS Start", value=branch.get("bqmsStartTime", "08:00"))
            if st.form_submit_button("Save Branch Info", type="primary"):
                branch.update({"name": b_name, "address": b_addr, "hours": b_hours,
                               "phone": b_phone, "openTime": b_open, "closeTime": b_close,
                               "bqmsStartTime": b_bqms})
                save_branch(branch)
                st.success("✅ Saved!"); st.rerun()

    # ── ANNOUNCEMENT ──
    with admin_tabs[4]:
        with st.form("announce_form"):
            ann = st.text_area("📢 Announcement (shown on Member Portal)",
                              value=branch.get("announcement", ""),
                              placeholder="e.g., Loan release delayed today.")
            if st.form_submit_button("Save Announcement", type="primary"):
                branch["announcement"] = ann
                save_branch(branch)
                st.success("✅ Announcement updated!"); st.rerun()

# ═══════════════════════════════════════════════════
#  DASHBOARD (TH/BH/DH)
# ═══════════════════════════════════════════════════
elif tab == "dash" and role in ("th", "bh", "dh"):
    st.subheader("📊 Dashboard")

    tot = len(res)
    done = len([r for r in res if r.get("status") == "COMPLETED"])
    ns = len([r for r in res if r.get("status") == "NO_SHOW"])
    onl = len([r for r in res if r.get("source") == "ONLINE"])
    ksk = len([r for r in res if r.get("source") == "KIOSK"])
    pri = len([r for r in res if r.get("priority") == "priority"])
    assigned = len([r for r in res if r.get("bqmsNumber")])
    nsr = f"{(ns/tot*100):.1f}" if tot else "0.0"
    da = f"{(onl/tot*100):.0f}" if tot else "0"

    dtabs = st.tabs(["📊 Overview", "🏷️ Service Mix", "💡 Insights", "📥 Export"])

    with dtabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="sss-metric" style="background:#E6F2FA;border-radius:8px;padding:12px;">
                <div class="value" style="color:#0066A1;">{tot}</div><div class="label">Total</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="sss-metric" style="background:#E8F8EF;border-radius:8px;padding:12px;">
                <div class="value" style="color:#0F9D58;">{done}</div><div class="label">Done</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="sss-metric" style="background:#FDEDEF;border-radius:8px;padding:12px;">
                <div class="value" style="color:#DC3545;">{ns}</div><div class="label">No-Show</div></div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Key Metrics**")
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("📱 Online Adoption", f"{da}%")
        with m2: st.metric("❌ No-Show Rate", f"{nsr}%")
        with m3: st.metric("🎫 BQMS Assigned", f"{(assigned/tot*100):.0f}%" if tot else "0%")

        st.markdown("---")
        st.markdown("**Channel Breakdown**")
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("📱 Online", onl)
        with c2: st.metric("🏢 Kiosk", ksk)
        with c3: st.metric("⭐ Priority", pri)

    with dtabs[1]:
        st.markdown("**Volume by Category**")
        for cat in cats:
            cnt = len([r for r in res if r.get("categoryId") == cat["id"]])
            s = sc.get(cat["id"], {"used": 0, "cap": cat["cap"]})
            pct = int((s["used"] / max(s["cap"], 1)) * 100)
            st.markdown(f"**{cat['icon']} {cat['short']}** — {cnt} entries ({pct}% utilized)")
            st.progress(min(pct / 100, 1.0))

    with dtabs[2]:
        st.markdown("**💡 Operational Insights**")
        da_val = int(da) if da else 0
        nsr_val = float(nsr) if nsr else 0

        if da_val < 40:
            st.markdown(f"""<div class="sss-alert" style="background:#FDEDEF;border-left:4px solid #DC3545;">
                📱 <strong>Online Adoption: {da}%</strong> — Needs more QR posters & member awareness campaigns.</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="sss-alert sss-alert-green">
                📱 <strong>Online Adoption: {da}%</strong> — Healthy adoption rate!</div>""", unsafe_allow_html=True)

        if nsr_val > 10:
            st.markdown(f"""<div class="sss-alert" style="background:#FDEDEF;border-left:4px solid #DC3545;">
                ❌ <strong>No-Show Rate: {nsr}%</strong> — Consider SMS reminders or tighter slots.</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="sss-alert sss-alert-green">
                ❌ <strong>No-Show Rate: {nsr}%</strong> — Within acceptable range.</div>""", unsafe_allow_html=True)

        if ksk > onl and tot > 5:
            st.markdown(f"""<div class="sss-alert sss-alert-yellow">
                🏢 <strong>Channel Mix:</strong> {ksk} kiosk vs {onl} online — Promote digital channel.</div>""", unsafe_allow_html=True)

    with dtabs[3]:
        st.markdown("**📥 Export Data**")
        # Today CSV
        csv_data = get_queue_csv(qdata)
        st.download_button("📥 Download Today's CSV", data=csv_data,
                          file_name=f"MabiliSSS_{today_str()}.csv",
                          mime="text/csv", use_container_width=True)

        st.markdown("---")
        st.markdown("**📁 Historical Data**")
        days = list_queue_days()
        if not days:
            st.info("No historical data yet.")
        else:
            for d in days[:14]:
                day_data = get_today_queue(d)
                day_csv = get_queue_csv(day_data)
                cnt = len(day_data.get("res", []))
                st.download_button(f"📅 {d} ({cnt} entries)", data=day_csv,
                                  file_name=f"MabiliSSS_{d}.csv", mime="text/csv",
                                  key=f"dl_{d}", use_container_width=True)

# ── FOOTER ──
st.markdown(f"""<div style="text-align:center;margin-top:40px;font-size:10px;color:#94A7B8;opacity:0.5;">
    RPT / SSS Gingoog Branch • MabiliSSS Queue {VER}</div>""", unsafe_allow_html=True)
