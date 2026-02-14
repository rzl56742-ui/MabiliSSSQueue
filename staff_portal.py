"""
═══════════════════════════════════════════════════════════════
 MabiliSSS Queue V1.0.0 — STAFF PORTAL (Streamlit)
 Authorized Personnel Only — Queue + Admin + Dashboard
 Run: streamlit run staff_portal.py --server.port 8502
 © RPT / SSS Gingoog Branch 2026
═══════════════════════════════════════════════════════════════
"""

import streamlit as st
import time as _time
from datetime import datetime
from shared_data import (
    VER, SSS_CSS, ROLE_META, OSTATUS_META,
    get_branch, save_branch, get_categories, save_categories,
    get_users, save_users, get_queue, save_queue,
    slot_counts, next_slot_num, is_duplicate, gen_id,
    today_iso, today_mmdd, build_csv, list_queue_days,
)

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="MabiliSSS Queue - Staff",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(SSS_CSS, unsafe_allow_html=True)

# ── SESSION STATE ──
_DEFAULTS = {
    "auth_user": None, "fail_count": 0, "lock_until": 0,
    "staff_tab": "queue", "last_activity": _time.time(),
}
for k, v in _DEFAULTS.items():
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
#  LOGIN
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
        submitted = st.form_submit_button("Login", type="primary",
                                           use_container_width=True, disabled=locked)
        if submitted and not locked:
            users = get_users()
            u = next((x for x in users
                      if x["username"].lower() == username.strip().lower()
                      and x.get("active", True)), None)
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
                touch()
                st.rerun()

    st.caption("Default password: **mnd2026** · Contact TH/SH for password reset.")
    st.markdown(f'<div class="sss-footer">{VER}</div>', unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════
#  AUTHENTICATED — Load all data
# ═══════════════════════════════════════════════════
touch()
user   = st.session_state.auth_user
role   = user["role"]
branch = get_branch()
cats   = get_categories()
users  = get_users()
qdata  = get_queue()
res    = qdata.get("res", [])
bqms_st= qdata.get("bqmsState", {})
o_stat = qdata.get("oStat", "online")
sc     = slot_counts(cats, res)
rm     = ROLE_META.get(role, {})
is_readonly = role in ("bh", "dh")

# ── HEADER ──
st.markdown(f"""<div class="sss-header">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div><h2>{rm.get('icon','')} MabiliSSS Staff</h2>
            <p>{user['displayName']} · {rm.get('label', role)}</p></div>
        <div style="text-align:right;font-size:12px;opacity:0.8;">
            {now.strftime('%I:%M %p')}<br/>{today_iso()}</div>
    </div>
</div>""", unsafe_allow_html=True)

# ── DYNAMIC NAV (only show tabs the role can access) ──
nav_items = [("📋 Queue", "queue")]
if role == "th":
    nav_items.append(("👔 Admin", "admin"))
if role in ("th", "bh", "dh"):
    nav_items.append(("📊 Dashboard", "dash"))
nav_items.append(("🔑 Password", "change_pw"))
nav_items.append(("🚪 Logout", "logout"))

nav_cols = st.columns(len(nav_items))
for i, (label, key) in enumerate(nav_items):
    with nav_cols[i]:
        if key == "logout":
            if st.button(label, use_container_width=True):
                st.session_state.auth_user = None
                st.rerun()
        else:
            btn_type = "primary" if st.session_state.staff_tab == key else "secondary"
            if st.button(label, use_container_width=True, type=btn_type):
                st.session_state.staff_tab = key
                st.rerun()

tab = st.session_state.staff_tab


# ═══════════════════════════════════════════════════
#  CHANGE PASSWORD
# ═══════════════════════════════════════════════════
if tab == "change_pw":
    st.subheader("🔑 Change Password")
    with st.form("pw_form"):
        new_pw  = st.text_input("New Password", type="password", help="Min 4 characters")
        new_pw2 = st.text_input("Confirm Password", type="password")
        if st.form_submit_button("Save Password", type="primary"):
            if len(new_pw) < 4:
                st.error("Min 4 characters.")
            elif new_pw != new_pw2:
                st.error("Passwords don't match.")
            else:
                all_u = get_users()
                for u in all_u:
                    if u["id"] == user["id"]:
                        u["password"] = new_pw
                save_users(all_u)
                st.session_state.auth_user["password"] = new_pw
                st.success("✅ Password changed!")
                st.session_state.staff_tab = "queue"
                st.rerun()


# ═══════════════════════════════════════════════════
#  QUEUE CONSOLE
# ═══════════════════════════════════════════════════
elif tab == "queue":
    unassigned = [r for r in res
                  if not r.get("bqmsNumber")
                  and r.get("status") not in ("NO_SHOW","COMPLETED")]

    if not is_readonly:
        # ── SYSTEM STATUS TOGGLE ──
        st.markdown("**System Status**")
        _stat_opts = ["🟢 Online", "🟡 Intermittent", "🔴 Offline"]
        _stat_map  = {"🟢 Online":"online", "🟡 Intermittent":"intermittent", "🔴 Offline":"offline"}
        _stat_rev  = {v:k for k,v in _stat_map.items()}
        cur_label  = _stat_rev.get(o_stat, "🟢 Online")
        new_stat   = st.radio("Reservation status:", _stat_opts, horizontal=True,
                              index=_stat_opts.index(cur_label))
        if _stat_map[new_stat] != o_stat:
            qdata["oStat"] = _stat_map[new_stat]
            save_queue(qdata)
            st.rerun()

        # ── UNASSIGNED ALERT ──
        if unassigned:
            st.markdown(f"""<div class="sss-alert sss-alert-red" style="font-size:16px;">
                🔴 <strong>{len(unassigned)} NEED BQMS#</strong> — Assign numbers below
            </div>""", unsafe_allow_html=True)

        # ── BQMS NOW SERVING ──
        with st.expander("🔄 BQMS — Now Serving (click to update)", expanded=False):
            with st.form("bqms_form"):
                new_bqms = dict(bqms_st)
                for i in range(0, len(cats), 2):
                    cols = st.columns(2)
                    for j, col in enumerate(cols):
                        idx = i + j
                        if idx >= len(cats):
                            break
                        c = cats[idx]
                        with col:
                            cur = bqms_st.get(c["id"], {}).get("nowServing", "")
                            val = st.text_input(f"{c['icon']} {c['short']}", value=cur,
                                                key=f"bqms_{c['id']}")
                            new_bqms[c["id"]] = {"nowServing": val.strip().upper()}
                if st.form_submit_button("Update Now Serving", type="primary",
                                          use_container_width=True):
                    qdata["bqmsState"] = new_bqms
                    save_queue(qdata)
                    st.success("✅ Updated!")
                    st.rerun()

        # ── WALK-IN REGISTRATION ──
        with st.expander("➕ Add Walk-in Member", expanded=False):
            with st.form("walkin_form"):
                # Category as selectbox
                cat_labels = ["-- Select Category --"] + [
                    f"{c['icon']} {c['label']} ({sc.get(c['id'],{}).get('remaining',0)} left)"
                    for c in cats
                ]
                w_cat_idx = st.selectbox("Category *", range(len(cat_labels)),
                                         format_func=lambda i: cat_labels[i],
                                         key="w_cat_sel")
                w_cat_obj = cats[w_cat_idx - 1] if w_cat_idx > 0 else None

                # Sub-service: show ALL possible services from ALL categories
                # but only match when we know the category after submit
                all_svcs = ["-- None --"]
                svc_map  = {}
                for c in cats:
                    for s in c.get("services", []):
                        label = f"{c['icon']} {s['label']}"
                        all_svcs.append(label)
                        svc_map[label] = {"catId": c["id"], "svcId": s["id"],
                                          "svcLabel": s["label"]}
                w_svc_idx = st.selectbox("Sub-service (optional)", range(len(all_svcs)),
                                          format_func=lambda i: all_svcs[i],
                                          key="w_svc_sel")
                w_svc_pick = svc_map.get(all_svcs[w_svc_idx]) if w_svc_idx > 0 else None

                wc1, wc2 = st.columns(2)
                with wc1: w_last  = st.text_input("Last Name *", key="wl")
                with wc2: w_first = st.text_input("First Name *", key="wf")
                wc1, wc2 = st.columns([1, 3])
                with wc1: w_mi  = st.text_input("M.I.", max_chars=2, key="wmi")
                with wc2: w_mob = st.text_input("Mobile (optional)", key="wmob")
                w_pri = st.radio("Lane:", ["👤 Regular", "⭐ Priority"],
                                 horizontal=True, key="wpri")
                w_bqms = ""
                if role != "kiosk":
                    w_bqms = st.text_input("BQMS # (if already issued)", key="wbqms",
                                           placeholder="Leave blank if not yet")

                if st.form_submit_button("Register Walk-in", type="primary",
                                          use_container_width=True):
                    wl = w_last.strip().upper()
                    wf = w_first.strip().upper()
                    wm = w_mob.strip()

                    errors = []
                    if not w_cat_obj:
                        errors.append("Select a category.")
                    if not wl:
                        errors.append("Last Name required.")
                    if not wf:
                        errors.append("First Name required.")

                    if errors:
                        for e in errors:
                            st.error(f"❌ {e}")
                    else:
                        fresh     = get_queue()
                        fresh_res = fresh.get("res", [])
                        s = slot_counts(cats, fresh_res).get(w_cat_obj["id"],
                            {"used":0, "cap": w_cat_obj["cap"]})

                        if is_duplicate(fresh_res, wl, wf, wm):
                            st.error("Duplicate: active reservation exists.")
                        elif s["remaining"] <= 0:
                            st.error("Cap reached for this category.")
                        else:
                            slot = next_slot_num(fresh_res)
                            rn   = f"K-{today_mmdd()}-{slot:03d}"
                            svc_label = "Walk-in"
                            svc_id    = "walkin"
                            if w_svc_pick and w_svc_pick["catId"] == w_cat_obj["id"]:
                                svc_label = w_svc_pick["svcLabel"]
                                svc_id    = w_svc_pick["svcId"]

                            bqms_val = w_bqms.strip().upper() if w_bqms else ""
                            entry = {
                                "id": gen_id(), "slot": slot, "resNum": rn,
                                "lastName": wl, "firstName": wf,
                                "mi": w_mi.strip().upper(), "mobile": wm,
                                "service": svc_label, "serviceId": svc_id,
                                "category": w_cat_obj["label"],
                                "categoryId": w_cat_obj["id"],
                                "catIcon": w_cat_obj["icon"],
                                "priority": "priority" if "Priority" in w_pri else "regular",
                                "status": "ARRIVED" if bqms_val else "RESERVED",
                                "bqmsNumber": bqms_val or None,
                                "source": "KIOSK",
                                "issuedAt": datetime.now().isoformat(),
                                "arrivedAt": datetime.now().isoformat() if bqms_val else None,
                                "completedAt": None,
                            }
                            fresh_res.append(entry)
                            fresh["res"] = fresh_res
                            save_queue(fresh)
                            st.success(f"✅ Registered: {rn}")
                            st.rerun()

    # ── FILTER BAR ──
    st.markdown("---")
    _filt_map = {
        "🔴 Need BQMS": "UNASSIGNED",
        "All": "all",
        "🏢 Kiosk": "KIOSK",
        "📱 Online": "ONLINE",
        "✅ Arrived": "ARRIVED",
        "✔ Done": "COMPLETED",
        "❌ No-Show": "NO_SHOW",
    }
    sel_f = st.radio("Filter:", list(_filt_map.keys()), horizontal=True, index=0)
    qf    = _filt_map[sel_f]

    search = st.text_input("🔍 Search by name, BQMS#, or Res#", key="qsearch")

    # Apply filters
    sorted_res = sorted(res, key=lambda r: (
        0 if not r.get("bqmsNumber") and r.get("status") not in ("NO_SHOW","COMPLETED") else 1,
        r.get("issuedAt", ""),
    ))
    filtered = sorted_res
    if qf == "UNASSIGNED":
        filtered = [r for r in filtered
                    if not r.get("bqmsNumber")
                    and r.get("status") not in ("NO_SHOW","COMPLETED")]
    elif qf == "KIOSK":
        filtered = [r for r in filtered if r.get("source") == "KIOSK"]
    elif qf == "ONLINE":
        filtered = [r for r in filtered if r.get("source") == "ONLINE"]
    elif qf != "all":
        filtered = [r for r in filtered if r.get("status") == qf]

    if search:
        s_lower = search.strip().lower()
        filtered = [r for r in filtered
                    if s_lower in r.get("lastName","").lower()
                    or s_lower in r.get("firstName","").lower()
                    or s_lower in (r.get("bqmsNumber","") or "").lower()
                    or s_lower in (r.get("resNum","") or "").lower()]

    st.caption(f"Showing {len(filtered)} entries")

    if not filtered:
        if qf == "UNASSIGNED":
            st.success("✅ All entries have BQMS numbers assigned!")
        else:
            st.info("No entries match this filter.")
    else:
        for r in filtered:
            needs_bqms = (not r.get("bqmsNumber")
                          and r.get("status") not in ("NO_SHOW","COMPLETED"))
            bdr = "#ef4444" if needs_bqms else "rgba(128,128,128,0.15)"
            src_icon = "🏢" if r.get("source") == "KIOSK" else "📱"
            pri_icon = "⭐" if r.get("priority") == "priority" else ""
            _slabels = {
                "RESERVED":"📋 RES", "ARRIVED":"✅ ARR", "SERVING":"🔵 SRV",
                "COMPLETED":"✅ DONE", "NO_SHOW":"❌ NS",
            }

            bqms_html = ""
            if r.get("bqmsNumber"):
                bqms_html = (f'<div style="font-family:monospace;font-size:20px;'
                             f'font-weight:900;color:#22B8CF;margin-top:4px;">'
                             f'BQMS: {r["bqmsNumber"]}</div>')

            st.markdown(f"""<div class="sss-card" style="border-left:4px solid {bdr};">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <span style="font-family:monospace;font-size:15px;font-weight:800;color:#3399CC;">
                            {r.get('resNum','')}</span>
                        <span style="font-size:11px;opacity:0.5;margin-left:6px;">{src_icon}</span>
                        {pri_icon}<br/>
                        <strong>{r.get('catIcon','')} {r['lastName']}, {r['firstName']} {r.get('mi','')}</strong><br/>
                        <span style="font-size:12px;opacity:0.6;">
                            {r.get('category','')} → {r.get('service','')}</span>
                        {f'<br/><span style="font-size:11px;opacity:0.5;">📱 {r["mobile"]}</span>' if r.get('mobile') else ''}
                    </div>
                    <div style="text-align:right;">
                        <span class="sss-badge" style="background:rgba(51,153,204,0.15);color:#3399CC;">
                            {_slabels.get(r['status'], r['status'])}</span>
                        {bqms_html}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # ── ACTION BUTTONS ──
            if not is_readonly:
                if needs_bqms:
                    ac1, ac2 = st.columns([3, 1])
                    with ac1:
                        bv = st.text_input("BQMS#", key=f"assign_{r['id']}",
                                           placeholder="e.g., L-023",
                                           label_visibility="collapsed")
                    with ac2:
                        if st.button("🎫 Assign", key=f"btn_a_{r['id']}",
                                     type="primary", use_container_width=True):
                            if bv.strip():
                                fresh = get_queue()
                                for fr in fresh["res"]:
                                    if fr["id"] == r["id"]:
                                        fr["bqmsNumber"] = bv.strip().upper()
                                        fr["status"] = "ARRIVED"
                                        fr["arrivedAt"] = datetime.now().isoformat()
                                save_queue(fresh)
                                st.rerun()
                            else:
                                st.warning("Enter a BQMS number first.")
                    if st.button("❌ No-Show", key=f"ns_{r['id']}",
                                 use_container_width=True):
                        fresh = get_queue()
                        for fr in fresh["res"]:
                            if fr["id"] == r["id"]:
                                fr["status"] = "NO_SHOW"
                        save_queue(fresh)
                        st.rerun()

                elif r.get("status") == "ARRIVED":
                    ac1, ac2, ac3 = st.columns(3)
                    with ac1:
                        if st.button("🔵 Serving", key=f"srv_{r['id']}",
                                     use_container_width=True):
                            fresh = get_queue()
                            for fr in fresh["res"]:
                                if fr["id"] == r["id"]: fr["status"] = "SERVING"
                            save_queue(fresh); st.rerun()
                    with ac2:
                        if st.button("✅ Complete", key=f"done_{r['id']}",
                                     use_container_width=True):
                            fresh = get_queue()
                            for fr in fresh["res"]:
                                if fr["id"] == r["id"]:
                                    fr["status"] = "COMPLETED"
                                    fr["completedAt"] = datetime.now().isoformat()
                            save_queue(fresh); st.rerun()
                    with ac3:
                        if st.button("❌ NS", key=f"ns2_{r['id']}",
                                     use_container_width=True):
                            fresh = get_queue()
                            for fr in fresh["res"]:
                                if fr["id"] == r["id"]: fr["status"] = "NO_SHOW"
                            save_queue(fresh); st.rerun()

                elif r.get("status") == "SERVING":
                    if st.button("✅ Complete", key=f"done2_{r['id']}",
                                 type="primary", use_container_width=True):
                        fresh = get_queue()
                        for fr in fresh["res"]:
                            if fr["id"] == r["id"]:
                                fr["status"] = "COMPLETED"
                                fr["completedAt"] = datetime.now().isoformat()
                        save_queue(fresh); st.rerun()

            st.markdown("")  # spacer between cards

    # Refresh
    st.markdown("---")
    if st.button("🔄 Refresh Queue", use_container_width=True):
        st.rerun()


# ═══════════════════════════════════════════════════
#  ADMIN PANEL (TH only)
# ═══════════════════════════════════════════════════
elif tab == "admin" and role == "th":
    st.subheader("👔 Admin Panel")
    admin_tabs = st.tabs(["👥 Users", "📋 Categories", "🔢 Caps",
                           "🏛️ Branch", "📢 Announcement"])

    # ────────────────────────────────────
    #  USERS
    # ────────────────────────────────────
    with admin_tabs[0]:
        st.markdown("**Staff Accounts**")
        st.caption("Default password: mnd2026")

        all_users = get_users()
        for u in all_users:
            rm_u = ROLE_META.get(u["role"], {})
            active_tag = "🟢" if u.get("active", True) else "🔴 Inactive"

            st.markdown(f"""<div class="sss-card">
                <strong>{rm_u.get('icon','')} {u['displayName']}</strong> {active_tag}<br/>
                <span style="font-size:11px;opacity:0.6;">
                    @{u['username']} · {rm_u.get('label', u['role'])}</span>
            </div>""", unsafe_allow_html=True)

            # Use a form PER user for safe editing
            with st.form(f"user_edit_{u['id']}"):
                uc1, uc2 = st.columns(2)
                with uc1:
                    new_name = st.text_input("Display Name", value=u["displayName"],
                                              key=f"uname_{u['id']}")
                with uc2:
                    role_keys = list(ROLE_META.keys())
                    new_role = st.selectbox(
                        "Role", role_keys,
                        index=role_keys.index(u["role"]),
                        key=f"urole_{u['id']}",
                        format_func=lambda x: f"{ROLE_META[x]['icon']} {ROLE_META[x]['label']}",
                    )
                uc3, uc4, uc5 = st.columns(3)
                with uc3:
                    save_btn = st.form_submit_button("💾 Save Changes")
                with uc4:
                    reset_btn = st.form_submit_button("🔑 Reset PW")
                with uc5:
                    toggle_btn = st.form_submit_button(
                        "🔴 Deactivate" if u.get("active", True) else "🟢 Activate"
                    )

                if save_btn:
                    fresh_u = get_users()
                    for x in fresh_u:
                        if x["id"] == u["id"]:
                            x["displayName"] = new_name.strip()
                            x["role"] = new_role
                    save_users(fresh_u)
                    st.success(f"✅ Updated {new_name}")
                    st.rerun()
                if reset_btn:
                    fresh_u = get_users()
                    for x in fresh_u:
                        if x["id"] == u["id"]: x["password"] = "mnd2026"
                    save_users(fresh_u)
                    st.success("✅ Password reset to mnd2026")
                    st.rerun()
                if toggle_btn:
                    fresh_u = get_users()
                    for x in fresh_u:
                        if x["id"] == u["id"]:
                            x["active"] = not x.get("active", True)
                    save_users(fresh_u)
                    st.rerun()

        # Add new user
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
                elif any(x["username"].lower() == nu_user.strip().lower()
                         for x in all_users):
                    st.error("Username already exists.")
                else:
                    fresh_u = get_users()
                    fresh_u.append({
                        "id": gen_id(),
                        "username": nu_user.strip().lower(),
                        "displayName": nu_name.strip(),
                        "role": nu_role,
                        "password": "mnd2026",
                        "active": True,
                    })
                    save_users(fresh_u)
                    st.success(f"✅ Added {nu_name} (@{nu_user})")
                    st.rerun()

    # ────────────────────────────────────
    #  CATEGORIES  (Edit / Add / Delete)
    # ────────────────────────────────────
    with admin_tabs[1]:
        st.markdown("**Service Categories** — Edit, add, or remove transaction types.")
        st.caption(f"Currently {len(cats)} categories configured.")

        for i, cat in enumerate(cats):
            s_info = sc.get(cat["id"], {"used": 0})
            with st.expander(
                f"{cat['icon']} {cat['label']} — {len(cat.get('services',[]))} subs "
                f"(cap: {cat['cap']}, used today: {s_info['used']})"
            ):
                with st.form(f"cat_edit_{i}"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        new_label = st.text_input("Label", value=cat["label"],
                                                   key=f"cl_{i}")
                    with ec2:
                        new_icon = st.text_input("Icon (emoji)", value=cat["icon"],
                                                  key=f"ci_{i}")
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        new_short = st.text_input("Short Name", value=cat["short"],
                                                   key=f"cs_{i}")
                    with ec2:
                        new_avg = st.number_input("Avg Time (min)",
                                                   value=cat["avgTime"],
                                                   min_value=1, key=f"ca_{i}")
                    with ec3:
                        new_cap = st.number_input("Daily Cap",
                                                   value=cat["cap"],
                                                   min_value=1, key=f"cc_{i}")

                    st.markdown("**Sub-transactions** (one per line):")
                    svc_text = "\n".join([s["label"] for s in cat.get("services", [])])
                    new_svcs_raw = st.text_area("Services:", value=svc_text,
                                                 key=f"csvcs_{i}")

                    sc1, sc2 = st.columns([3, 1])
                    with sc1:
                        save_cat_btn = st.form_submit_button("💾 Save Category",
                                                              type="primary")
                    with sc2:
                        del_cat_btn = st.form_submit_button("🗑️ Delete")

                    if save_cat_btn:
                        new_svcs = []
                        for line in new_svcs_raw.strip().split("\n"):
                            if line.strip():
                                sid = (line.strip().lower()
                                       .replace(" ", "_").replace("/", "_")[:20])
                                new_svcs.append({"id": sid, "label": line.strip()})
                        if not new_svcs:
                            st.error("At least one sub-transaction required.")
                        else:
                            fresh_cats = get_categories()
                            if i < len(fresh_cats):
                                fresh_cats[i] = {
                                    **cat,
                                    "label": new_label, "icon": new_icon,
                                    "short": new_short,
                                    "avgTime": int(new_avg), "cap": int(new_cap),
                                    "services": new_svcs,
                                }
                                save_categories(fresh_cats)
                                st.success("✅ Saved!")
                                st.rerun()

                    if del_cat_btn:
                        if s_info["used"] > 0:
                            st.error(
                                f"Cannot delete — {s_info['used']} active entries "
                                f"today under this category. Complete or no-show "
                                f"them first, or wait until tomorrow."
                            )
                        else:
                            fresh_cats = get_categories()
                            if i < len(fresh_cats):
                                removed = fresh_cats.pop(i)
                                save_categories(fresh_cats)
                                st.success(
                                    f"✅ Deleted: {removed['icon']} {removed['label']}"
                                )
                                st.rerun()

        # ── ADD NEW CATEGORY ──
        st.markdown("---")
        st.markdown("**➕ Add New Category**")
        with st.form("add_cat_form"):
            nc1, nc2 = st.columns(2)
            with nc1:
                nc_label = st.text_input("Category Name *",
                                          placeholder="e.g., EC / Maternity Subsidy")
            with nc2:
                nc_icon = st.text_input("Icon (emoji) *",
                                         placeholder="e.g., 🏥", value="📋")
            nc1, nc2, nc3 = st.columns(3)
            with nc1:
                nc_short = st.text_input("Short Name *",
                                          placeholder="e.g., EC/Mat")
            with nc2:
                nc_avg = st.number_input("Avg Time (min)", value=10,
                                          min_value=1, key="nc_avg")
            with nc3:
                nc_cap = st.number_input("Daily Cap", value=30,
                                          min_value=1, key="nc_cap")
            nc_svcs = st.text_area(
                "Sub-transactions * (one per line)",
                placeholder="Filing\nFollow-up\nInquiry",
                key="nc_svcs",
            )

            if st.form_submit_button("➕ Add Category", type="primary"):
                if not nc_label.strip() or not nc_short.strip():
                    st.error("Category Name and Short Name required.")
                elif not nc_svcs.strip():
                    st.error("At least one sub-transaction required.")
                else:
                    cat_id = (nc_label.strip().lower()
                              .replace(" ", "_").replace("/", "_")[:20])
                    # Check for duplicate ID
                    fresh_cats = get_categories()
                    if any(c["id"] == cat_id for c in fresh_cats):
                        st.error("A category with a similar name already exists.")
                    else:
                        new_svcs = []
                        for line in nc_svcs.strip().split("\n"):
                            if line.strip():
                                sid = (line.strip().lower()
                                       .replace(" ", "_").replace("/", "_")[:20])
                                new_svcs.append({"id": sid, "label": line.strip()})
                        fresh_cats.append({
                            "id": cat_id,
                            "label": nc_label.strip(),
                            "icon": nc_icon.strip() or "📋",
                            "short": nc_short.strip(),
                            "avgTime": int(nc_avg),
                            "cap": int(nc_cap),
                            "services": new_svcs,
                        })
                        save_categories(fresh_cats)
                        st.success(
                            f"✅ Added: {nc_icon.strip()} {nc_label.strip()} "
                            f"with {len(new_svcs)} sub-transactions"
                        )
                        st.rerun()

    # ────────────────────────────────────
    #  CAPS
    # ────────────────────────────────────
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
                fresh_cats = get_categories()
                for fc in fresh_cats:
                    if fc["id"] in new_caps:
                        fc["cap"] = new_caps[fc["id"]]
                save_categories(fresh_cats)
                st.success("✅ Caps updated!")
                st.rerun()

    # ────────────────────────────────────
    #  BRANCH
    # ────────────────────────────────────
    with admin_tabs[3]:
        with st.form("branch_form"):
            b_name  = st.text_input("Branch Name", value=branch["name"])
            b_addr  = st.text_input("Address", value=branch["address"])
            b_hours = st.text_input("Hours", value=branch["hours"])
            b_phone = st.text_input("Phone", value=branch.get("phone",""))
            bc1, bc2, bc3 = st.columns(3)
            with bc1: b_open = st.text_input("Res. Open", value=branch.get("openTime","06:00"))
            with bc2: b_close= st.text_input("Res. Close", value=branch.get("closeTime","16:00"))
            with bc3: b_bqms = st.text_input("BQMS Start", value=branch.get("bqmsStartTime","08:00"))
            if st.form_submit_button("Save Branch Info", type="primary"):
                branch.update({
                    "name": b_name, "address": b_addr, "hours": b_hours,
                    "phone": b_phone, "openTime": b_open, "closeTime": b_close,
                    "bqmsStartTime": b_bqms,
                })
                save_branch(branch)
                st.success("✅ Saved!")
                st.rerun()

    # ────────────────────────────────────
    #  ANNOUNCEMENT
    # ────────────────────────────────────
    with admin_tabs[4]:
        with st.form("announce_form"):
            ann = st.text_area("📢 Announcement (shown on Member Portal)",
                               value=branch.get("announcement",""),
                               placeholder="e.g., Loan release delayed today.")
            if st.form_submit_button("Save Announcement", type="primary"):
                branch["announcement"] = ann
                save_branch(branch)
                st.success("✅ Announcement updated!")
                st.rerun()


# ═══════════════════════════════════════════════════
#  DASHBOARD (TH / BH / DH)
# ═══════════════════════════════════════════════════
elif tab == "dash" and role in ("th", "bh", "dh"):
    st.subheader("📊 Dashboard")

    tot  = len(res)
    done = len([r for r in res if r.get("status") == "COMPLETED"])
    ns   = len([r for r in res if r.get("status") == "NO_SHOW"])
    onl  = len([r for r in res if r.get("source") == "ONLINE"])
    ksk  = len([r for r in res if r.get("source") == "KIOSK"])
    pri  = len([r for r in res if r.get("priority") == "priority"])
    assigned = len([r for r in res if r.get("bqmsNumber")])
    nsr_val  = (ns / tot * 100) if tot else 0
    da_val   = (onl / tot * 100) if tot else 0

    dtabs = st.tabs(["📊 Overview", "🏷️ Service Mix", "💡 Insights", "📥 Export"])

    with dtabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="sss-metric">
                <div class="val" style="color:#3399CC;">{tot}</div>
                <div class="lbl">Total</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="sss-metric">
                <div class="val" style="color:#22c55e;">{done}</div>
                <div class="lbl">Completed</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="sss-metric">
                <div class="val" style="color:#ef4444;">{ns}</div>
                <div class="lbl">No-Show</div></div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Key Metrics**")
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("📱 Online Adoption", f"{da_val:.0f}%")
        with m2: st.metric("❌ No-Show Rate", f"{nsr_val:.1f}%")
        with m3: st.metric("🎫 BQMS Assigned",
                           f"{(assigned/tot*100):.0f}%" if tot else "0%")

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
            s   = sc.get(cat["id"], {"used":0, "cap": cat["cap"]})
            pct = int((s["used"] / max(s["cap"], 1)) * 100)
            st.markdown(f"**{cat['icon']} {cat['short']}** — {cnt} entries ({pct}% utilized)")
            st.progress(min(pct / 100, 1.0))

    with dtabs[2]:
        st.markdown("**💡 Operational Insights**")
        if da_val < 40:
            st.markdown(f"""<div class="sss-alert sss-alert-red">
                📱 <strong>Online Adoption: {da_val:.0f}%</strong> — Needs more QR posters
                and member awareness campaigns.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="sss-alert sss-alert-green">
                📱 <strong>Online Adoption: {da_val:.0f}%</strong> — Healthy adoption rate!
            </div>""", unsafe_allow_html=True)

        if nsr_val > 10:
            st.markdown(f"""<div class="sss-alert sss-alert-red">
                ❌ <strong>No-Show Rate: {nsr_val:.1f}%</strong> — Consider SMS reminders
                or tighter slots.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="sss-alert sss-alert-green">
                ❌ <strong>No-Show Rate: {nsr_val:.1f}%</strong> — Within acceptable range.
            </div>""", unsafe_allow_html=True)

        if ksk > onl and tot > 5:
            st.markdown(f"""<div class="sss-alert sss-alert-yellow">
                🏢 <strong>Channel Mix:</strong> {ksk} kiosk vs {onl} online —
                Promote digital channel.
            </div>""", unsafe_allow_html=True)

    with dtabs[3]:
        st.markdown("**📥 Export Data**")
        csv_data = build_csv(qdata)
        st.download_button("📥 Download Today's CSV", data=csv_data,
                           file_name=f"MabiliSSS_{today_iso()}.csv",
                           mime="text/csv", use_container_width=True)

        st.markdown("---")
        st.markdown("**📁 Historical Data**")
        days = list_queue_days()
        if not days:
            st.info("No historical data yet.")
        else:
            for d in days[:14]:
                day_data = get_queue(d)
                day_csv  = build_csv(day_data)
                cnt = len(day_data.get("res", []))
                st.download_button(
                    f"📅 {d} ({cnt} entries)", data=day_csv,
                    file_name=f"MabiliSSS_{d}.csv", mime="text/csv",
                    key=f"dl_{d}", use_container_width=True,
                )


# ═══════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════
st.markdown(f'<div class="sss-footer">RPT / SSS Gingoog Branch · MabiliSSS Queue {VER}</div>',
    unsafe_allow_html=True)
