# 🏛️ MabiliSSS Queue V1.0.0

**Digital Priority Number Issuance System**  
SSS Gingoog Branch — Streamlit Edition  
© RPT / SSS Gingoog Branch 2026

---

## 📁 Project Structure

```
MabiliSSS-Queue/
├── shared_data.py        # Shared data layer (JSON storage)
├── member_portal.py      # Member Portal (public — reserve & track)
├── staff_portal.py       # Staff Portal (auth required — queue mgmt)
├── requirements.txt      # Python dependencies
├── .streamlit/
│   └── config.toml       # Streamlit theme config
├── data/                  # Auto-created: JSON data storage
└── README.md
```

## 🚀 Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR-USERNAME/MabiliSSS-Queue.git
cd MabiliSSS-Queue

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Member Portal (port 8501)
streamlit run member_portal.py --server.port 8501

# 4. In a NEW terminal, run Staff Portal (port 8502)
streamlit run staff_portal.py --server.port 8502
```

- **Member Portal:** http://localhost:8501
- **Staff Portal:** http://localhost:8502

## 🔐 Default Staff Accounts

| Username | Display Name    | Role              | Password  |
|----------|-----------------|-------------------|-----------|
| `kiosk`  | Guard / Kiosk   | Kiosk (Guard)     | `mnd2026` |
| `staff1` | Staff 1         | Staff In-Charge   | `mnd2026` |
| `staff2` | Staff 2         | Staff In-Charge   | `mnd2026` |
| `th`     | Team Head       | Team Head / SH    | `mnd2026` |
| `bh`     | Branch Head     | Branch Head       | `mnd2026` |
| `dh`     | Division Head   | Division Head     | `mnd2026` |

> ⚠️ **Change all passwords on first login!**

## ☁️ Deploy to Streamlit Cloud

### Option A: Two Separate Apps (Recommended)

1. **Create TWO GitHub repos:**
   - `MabiliSSS-Member` (member_portal.py + shared_data.py + requirements.txt)
   - `MabiliSSS-Staff` (staff_portal.py + shared_data.py + requirements.txt)

2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy each repo as a separate app
4. Share the Member Portal URL with the public

### Option B: Single Repo with Entry Points

1. Push this entire repo to GitHub
2. Deploy `member_portal.py` as the main app
3. For staff access, deploy the same repo again selecting `staff_portal.py`

## 📋 Features

### Member Portal
- Online slot reservation (no login needed)
- Real-time queue tracking by mobile or reservation number
- BQMS number display with wait time estimates
- RA 10173 data privacy compliance
- Auto-refresh on demand

### Staff Portal
- Password-based authentication with lockout protection
- Walk-in registration (Kiosk mode)
- BQMS number assignment workflow
- Queue management (Serving → Complete → No-Show)
- Now Serving tracker per category
- Online/Offline system toggle
- User management (TH/SH: add, edit names, reset passwords)
- Category & cap configuration
- Analytics dashboard with CSV export

## 🔄 How Data Syncs

Both portals read/write to the same `data/` directory:
- `data/branch.json` — branch configuration
- `data/categories.json` — service categories
- `data/users.json` — staff accounts
- `data/queue_YYYY-MM-DD.json` — daily queue data

This means **both apps must run on the same server** for data to sync.

## 📌 Notes

- For Streamlit Cloud: persistent storage resets on reboot. 
  For production, consider upgrading to a database backend (SQLite/PostgreSQL).
- The `data/` folder is auto-created on first run.
- File locking works on Linux/Mac. Windows users also supported (no locking).
