"""
═══════════════════════════════════════════════════════════════
 MabiliSSS Queue V1.0.0 — SHARED DATA LAYER
 JSON-based persistent storage for both portals
 © RPT / SSS Gingoog Branch 2026
═══════════════════════════════════════════════════════════════
"""

import json, os, time, uuid, hashlib
from datetime import datetime, date
from pathlib import Path

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False  # Windows fallback

VER = "V1.0.0"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ── FILE PATHS ──
BRANCH_FILE = DATA_DIR / "branch.json"
CATS_FILE = DATA_DIR / "categories.json"
USERS_FILE = DATA_DIR / "users.json"

def queue_file(d=None):
    d = d or date.today().isoformat()
    return DATA_DIR / f"queue_{d}.json"

# ── DEFAULTS ──
DEF_BRANCH = {
    "name": "SSS Gingoog Branch",
    "address": "National Highway, Gingoog City, Misamis Oriental",
    "hours": "Mon–Fri, 8:00 AM — 5:00 PM",
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
    "kiosk": {"label": "Kiosk (Guard)", "icon": "🏢", "level": 0},
    "staff": {"label": "Staff In-Charge", "icon": "🛡️", "level": 1},
    "th": {"label": "Team Head / Section Head", "icon": "👔", "level": 2},
    "bh": {"label": "Branch Head", "icon": "🏛️", "level": 3},
    "dh": {"label": "Division Head", "icon": "⭐", "level": 4},
}

OSTATUS_MAP = {
    "online": {"label": "🟢 Reservation Open", "color": "green"},
    "intermittent": {"label": "🟡 Intermittent — Expect Delays", "color": "orange"},
    "offline": {"label": "🔴 Reservation Closed", "color": "red"},
}

# ── THREAD-SAFE JSON IO ──
def _read_json(path, default):
    if not path.exists():
        _write_json(path, default)
        return default
    try:
        with open(path, "r") as f:
            if HAS_FCNTL:
                fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
            if HAS_FCNTL:
                fcntl.flock(f, fcntl.LOCK_UN)
            return data
    except Exception:
        return default

def _write_json(path, data):
    try:
        tmp = str(path) + ".tmp"
        with open(tmp, "w") as f:
            if HAS_FCNTL:
                fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(data, f, indent=2, default=str)
            if HAS_FCNTL:
                fcntl.flock(f, fcntl.LOCK_UN)
        os.replace(tmp, path)
        return True
    except Exception:
        return False

# ── PUBLIC API ──
def get_branch():
    return _read_json(BRANCH_FILE, DEF_BRANCH)

def save_branch(data):
    return _write_json(BRANCH_FILE, data)

def get_categories():
    return _read_json(CATS_FILE, DEF_CATS)

def save_categories(data):
    return _write_json(CATS_FILE, data)

def get_users():
    return _read_json(USERS_FILE, DEF_USERS)

def save_users(data):
    return _write_json(USERS_FILE, data)

def get_today_queue(d=None):
    default = {"res": [], "bqmsState": {}, "oStat": "online", "date": d or date.today().isoformat()}
    return _read_json(queue_file(d), default)

def save_today_queue(data, d=None):
    data["date"] = d or date.today().isoformat()
    return _write_json(queue_file(d), data)

def list_queue_days():
    days = []
    for f in DATA_DIR.glob("queue_*.json"):
        d = f.stem.replace("queue_", "")
        days.append(d)
    return sorted(days, reverse=True)

# ── HELPERS ──
def gen_id():
    return f"{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}"

def today_str():
    return date.today().isoformat()

def today_short():
    return date.today().strftime("%m%d")

def slot_counts(cats, res):
    m = {}
    for c in cats:
        active = [r for r in res if r.get("categoryId") == c["id"] and r.get("status") != "NO_SHOW"]
        used = len(active)
        cap = c.get("cap", 50)
        m[c["id"]] = {"used": used, "cap": cap, "remaining": max(0, cap - used)}
    return m

def is_duplicate(res, last, first, mob):
    nk = f"{last.strip().upper()}|{first.strip().upper()}"
    for r in res:
        if r.get("status") in ("NO_SHOW", "COMPLETED"):
            continue
        existing_nk = f"{r.get('lastName','')}|{r.get('firstName','')}"
        if existing_nk == nk:
            return True
        if mob and r.get("mobile") and r["mobile"] == mob.strip():
            return True
    return False

def format_bqms_time(t_str):
    try:
        parts = t_str.split(":")
        h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        ampm = "PM" if h >= 12 else "AM"
        h12 = h % 12 or 12
        return f"{h12}:{m:02d} {ampm}"
    except Exception:
        return "8:00 AM"

def get_queue_csv(data):
    """Generate CSV string from queue data."""
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    branch = get_branch()
    writer.writerow(["MabiliSSS Queue — Daily Report"])
    writer.writerow([f"Branch: {branch['name']}"])
    writer.writerow([f"Date: {data.get('date', today_str())}"])
    writer.writerow([])
    writer.writerow(["Res#","Slot","Source","LastName","FirstName","MI","Mobile",
                     "Category","Service","Priority","Status","BQMS#",
                     "ReservedAt","ArrivedAt","CompletedAt"])
    for r in data.get("res", []):
        writer.writerow([
            r.get("resNum",""), r.get("slot",""), r.get("source",""),
            r.get("lastName",""), r.get("firstName",""), r.get("mi",""),
            r.get("mobile",""), r.get("category",""), r.get("service",""),
            r.get("priority",""), r.get("status",""), r.get("bqmsNumber",""),
            r.get("issuedAt",""), r.get("arrivedAt",""), r.get("completedAt",""),
        ])
    return output.getvalue()

# ── CUSTOM CSS ──
SSS_CSS = """
<style>
    .stApp { background-color: #EFF5FA; }
    [data-testid="stHeader"] { background-color: #002E52; }
    .sss-header { background: linear-gradient(135deg, #002E52, #0066A1); color: white;
        padding: 16px 20px; border-radius: 10px; margin-bottom: 16px; }
    .sss-header h2 { margin: 0; font-size: 22px; }
    .sss-header p { margin: 4px 0 0; opacity: 0.7; font-size: 13px; }
    .sss-card { background: white; border-radius: 10px; padding: 16px; margin-bottom: 12px;
        border: 1px solid #D6E4EE; }
    .sss-metric { text-align: center; padding: 12px; border-radius: 8px; }
    .sss-metric .value { font-size: 28px; font-weight: 800; }
    .sss-metric .label { font-size: 11px; color: #5A7184; margin-top: 2px; }
    .sss-alert { border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; font-weight: 700; }
    .sss-alert-red { background: linear-gradient(135deg, #DC3545, #B91C1C); color: white; }
    .sss-alert-green { background: #E8F8EF; color: #166534; border: 1px solid #0F9D58; }
    .sss-alert-blue { background: #DBEAFE; color: #1E40AF; border: 1px solid #3B82F6; }
    .sss-alert-yellow { background: #FFF9E6; color: #92400E; border: 1px solid #D97706; }
    .sss-badge { display: inline-block; padding: 2px 8px; border-radius: 6px;
        font-size: 11px; font-weight: 700; }
    .sss-bqms { font-family: monospace; font-size: 32px; font-weight: 900; color: #0891B2; text-align: center; }
    .sss-resnum { font-family: monospace; font-size: 24px; font-weight: 900; color: #0066A1; text-align: center; }
    div[data-testid="stVerticalBlock"] > div:has(> .sss-header) { padding: 0; }
    .stButton > button { border-radius: 8px; font-weight: 700; }
</style>
"""
