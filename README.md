# MabiliSSS Queue V1.0.0

**Digital Priority Number Issuance System — SSS Gingoog Branch**

## Quick Start (Local Laptop Pilot)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch both portals

**Terminal 1 — Member Portal (public-facing):**
```bash
streamlit run member_portal.py --server.port 8501
```

**Terminal 2 — Staff Portal (authenticated):**
```bash
streamlit run staff_portal.py --server.port 8502
```

### 3. Open in browser
- Member: http://localhost:8501
- Staff: http://localhost:8502

## Default Staff Accounts

| Username | Role | Password |
|----------|------|----------|
| kiosk | Guard / Kiosk | mnd2026 |
| staff1 | Staff In-Charge | mnd2026 |
| staff2 | Staff In-Charge | mnd2026 |
| th | Team Head | mnd2026 |
| bh | Branch Head | mnd2026 |
| dh | Division Head | mnd2026 |

## How Data Sync Works

Both portals read/write the same `data/` folder (anchored to the script directory).
When a member reserves on port 8501, staff sees it instantly on port 8502 (on refresh).
When staff assigns a BQMS number, the member tracker auto-refreshes every 20 seconds.

## Features

- Online reservation + walk-in kiosk registration
- Live queue tracking with auto-refresh (20s)
- BQMS number assignment workflow
- Role-based access control (5 roles)
- Admin panel: users, categories, caps, branch settings, announcements
- Dashboard: KPIs, service mix, operational insights
- CSV export (today + 14 days historical)
- Dark/light mode adaptive UI
- RA 10173 data privacy compliance
- Session timeout (30 min) + 3-attempt lockout

---
© RPT / SSS Gingoog Branch 2026
