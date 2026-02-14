"""
═══════════════════════════════════════════════════════════════
 MabiliSSS Queue V1.0.0 — SHARED DATA LAYER
 JSON file storage shared by both Member + Staff portals.
 Both portals import this file → same data directory → synced.
 © RPT / SSS Gingoog Branch 2026
═══════════════════════════════════════════════════════════════
"""

import json, os, time, uuid, csv, io
from datetime import datetime, date
from pathlib import Path

try:
    import fcntl
    _HAS_FCNTL = True
except ImportError:
    _HAS_FCNTL = False  # Windows

VER = "V1.0.0"

# ── CRITICAL: absolute path anchored to THIS file's location ──
# Both portals import shared_data → same directory → same data/
_SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = _SCRIPT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

BRANCH_FILE = DATA_DIR / "branch.json"
CATS_FILE   = DATA_DIR / "categories.json"
USERS_FILE  = DATA_DIR / "users.json"

def _queue_file(d=None):
    d = d or date.today().isoformat()
    return DATA_DIR / f"queue_{d}.json"

# ═══════════════════════════════════════════════════
#  DEFAULTS
# ═══════════════════════════════════════════════════
DEF_BRANCH = {
    "name": "SSS Gingoog Branch",
    "address": "National Highway, Gingoog City, Misamis Oriental",
    "hours": "Mon-Fri, 8:00 AM - 5:00 PM",
    "phone": "",
    "openTime": "06:00",
    "closeTime": "16:00",
    "bqmsStartTime": "08:00",
    "announcement": "",
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

ROLE_META = {
    "kiosk": {"label":"Kiosk (Guard)",           "icon":"🏢", "level":0},
    "staff": {"label":"Staff In-Charge",         "icon":"🛡️", "level":1},
    "th":    {"label":"Team Head / Section Head", "icon":"👔", "level":2},
    "bh":    {"label":"Branch Head",             "icon":"🏛️", "level":3},
    "dh":    {"label":"Division Head",           "icon":"⭐", "level":4},
}

OSTATUS_META = {
    "online":       {"label":"Reservation Open",              "emoji":"🟢"},
    "intermittent": {"label":"Intermittent - Expect Delays",  "emoji":"🟡"},
    "offline":      {"label":"Reservation Closed",            "emoji":"🔴"},
}

# ═══════════════════════════════════════════════════
#  FILE I/O  (thread-safe with flock on Linux/Mac)
# ═══════════════════════════════════════════════════
def _read(path, default):
    if not path.exists():
        _write(path, default)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            if _HAS_FCNTL: fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
            if _HAS_FCNTL: fcntl.flock(f, fcntl.LOCK_UN)
            return data
    except Exception:
        return default

def _write(path, data):
    try:
        tmp = str(path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            if _HAS_FCNTL: fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            if _HAS_FCNTL: fcntl.flock(f, fcntl.LOCK_UN)
        os.replace(tmp, str(path))
        return True
    except Exception:
        return False

# ═══════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════
def get_branch():        return _read(BRANCH_FILE, DEF_BRANCH)
def save_branch(d):      return _write(BRANCH_FILE, d)
def get_categories():    return _read(CATS_FILE, DEF_CATS)
def save_categories(d):  return _write(CATS_FILE, d)
def get_users():         return _read(USERS_FILE, DEF_USERS)
def save_users(d):       return _write(USERS_FILE, d)

def get_queue(d=None):
    default = {"res":[], "bqmsState":{}, "oStat":"online",
               "date": d or date.today().isoformat()}
    return _read(_queue_file(d), default)

def save_queue(data, d=None):
    data["date"] = d or date.today().isoformat()
    return _write(_queue_file(d), data)

def list_queue_days():
    days = []
    for f in DATA_DIR.glob("queue_*.json"):
        days.append(f.stem.replace("queue_", ""))
    return sorted(days, reverse=True)

# ═══════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════
def gen_id():
    return f"{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}"

def today_iso():
    return date.today().isoformat()

def today_mmdd():
    return date.today().strftime("%m%d")

def slot_counts(cats, res_list):
    """Active count + cap for each category. NO_SHOW excluded from 'used'."""
    m = {}
    for c in cats:
        active = [r for r in res_list
                  if r.get("categoryId") == c["id"]
                  and r.get("status") != "NO_SHOW"]
        used = len(active)
        cap  = c.get("cap", 50)
        m[c["id"]] = {"used":used, "cap":cap, "remaining":max(0, cap - used)}
    return m

def next_slot_num(res_list):
    """GLOBAL sequential slot# — counts ALL entries (incl NO_SHOW/COMPLETED)
    to guarantee unique reservation numbers."""
    return len(res_list) + 1

def is_duplicate(res_list, last, first, mob):
    nk = f"{last.strip().upper()}|{first.strip().upper()}"
    for r in res_list:
        if r.get("status") in ("NO_SHOW", "COMPLETED"):
            continue
        ek = f"{r.get('lastName','')}|{r.get('firstName','')}"
        if ek == nk:
            return True
        if mob and r.get("mobile") and r["mobile"] == mob.strip():
            return True
    return False

def format_time_12h(t24):
    try:
        parts = t24.split(":")
        h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        return f"{h % 12 or 12}:{m:02d} {'PM' if h >= 12 else 'AM'}"
    except Exception:
        return "8:00 AM"

def build_csv(qdata):
    """Generate CSV string from a day's queue data."""
    out = io.StringIO()
    w = csv.writer(out)
    br = get_branch()
    w.writerow(["MabiliSSS Queue - Daily Report"])
    w.writerow([f"Branch: {br['name']}"])
    w.writerow([f"Date: {qdata.get('date', today_iso())}"])
    w.writerow([])
    w.writerow(["Res#","Slot","Source","LastName","FirstName","MI","Mobile",
                "Category","Service","Priority","Status","BQMS#",
                "ReservedAt","ArrivedAt","CompletedAt"])
    for r in qdata.get("res", []):
        w.writerow([
            r.get("resNum",""), r.get("slot",""), r.get("source",""),
            r.get("lastName",""), r.get("firstName",""), r.get("mi",""),
            r.get("mobile",""), r.get("category",""), r.get("service",""),
            r.get("priority",""), r.get("status",""), r.get("bqmsNumber",""),
            r.get("issuedAt",""), r.get("arrivedAt",""), r.get("completedAt",""),
        ])
    return out.getvalue()

# ═══════════════════════════════════════════════════
#  CSS — DARK/LIGHT ADAPTIVE
#  Uses Streamlit CSS variables so colours auto-switch.
#  Header/banner always has forced dark-blue bg + white text.
# ═══════════════════════════════════════════════════
SSS_CSS = """
<style>
/* ── Reset & Base ── */
.sss-header {
    background: linear-gradient(135deg, #002E52 0%, #0066A1 100%);
    color: #FFFFFF !important;
    padding: 18px 22px; border-radius: 12px; margin-bottom: 16px;
}
.sss-header h2 { margin:0; font-size:22px; color:#FFFFFF !important; }
.sss-header p  { margin:4px 0 0; opacity:0.75; font-size:13px; color:#FFFFFF !important; }

/* ── Cards — adapt to Streamlit theme ── */
.sss-card {
    background: var(--secondary-background-color, #ffffff);
    color: var(--text-color, #1a1a2e);
    border-radius: 10px; padding: 16px; margin-bottom: 12px;
    border: 1px solid rgba(128,128,128,0.15);
}
.sss-card strong, .sss-card b { color: var(--text-color, #1a1a2e); }

/* ── Metrics ── */
.sss-metric {
    text-align:center; padding:14px 8px; border-radius:10px;
    background: var(--secondary-background-color, #f5f5f5);
    border: 1px solid rgba(128,128,128,0.1);
}
.sss-metric .val { font-size:30px; font-weight:900; line-height:1.2; }
.sss-metric .lbl { font-size:11px; opacity:0.6; margin-top:2px; }

/* ── Alerts ── */
.sss-alert {
    border-radius:8px; padding:12px 16px; margin-bottom:12px;
    font-weight:600; text-align:center;
}
.sss-alert-red    { background:rgba(220,53,69,0.15); color:#ef4444; border:1px solid rgba(220,53,69,0.3); }
.sss-alert-green  { background:rgba(15,157,88,0.12); color:#22c55e; border:1px solid rgba(15,157,88,0.25); }
.sss-alert-blue   { background:rgba(59,130,246,0.12); color:#60a5fa; border:1px solid rgba(59,130,246,0.25); }
.sss-alert-yellow { background:rgba(217,119,6,0.12); color:#f59e0b; border:1px solid rgba(217,119,6,0.25); }

/* Force strong/b inside alerts to inherit alert color */
.sss-alert strong, .sss-alert b { color: inherit; }

/* ── Badges ── */
.sss-badge {
    display:inline-block; padding:3px 10px; border-radius:6px;
    font-size:11px; font-weight:700;
}

/* ── Big numbers ── */
.sss-bqms  { font-family:monospace; font-size:36px; font-weight:900; color:#22B8CF; text-align:center; }
.sss-resnum{ font-family:monospace; font-size:26px; font-weight:900; color:#3399CC; text-align:center; }

/* ── Table rows inside cards ── */
.sss-card td { color: var(--text-color, #1a1a2e); padding: 4px 0; }
.sss-card td.muted { opacity: 0.6; }

/* ── Buttons ── */
.stButton > button { border-radius:8px; font-weight:700; }

/* ── Footer ── */
.sss-footer { text-align:center; margin-top:40px; font-size:11px; opacity:0.4;
    color: var(--text-color, #888); }
</style>
"""
