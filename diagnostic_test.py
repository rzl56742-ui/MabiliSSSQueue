"""
═══════════════════════════════════════════════════════════════
 MabiliSSS Queue — DIAGNOSTIC TEST
 Run this BEFORE the portals to verify everything is connected.
 Usage: python3 diagnostic_test.py
═══════════════════════════════════════════════════════════════
"""
import os, sys, json, time
from pathlib import Path

# Ensure we import from the same directory as this script
sys.path.insert(0, str(Path(__file__).resolve().parent))

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

results = []

def test(name, passed, detail=""):
    status = PASS if passed else FAIL
    results.append((name, passed))
    print(f"  {status} {name}" + (f" → {detail}" if detail else ""))

print("═══════════════════════════════════════════════════")
print("  MabiliSSS Queue — Connection Diagnostic")
print("═══════════════════════════════════════════════════")
print()

# ── TEST 1: Can we import shared_data? ──
print("▶ 1. MODULE IMPORTS")
try:
    from shared_data import (
        DATA_DIR, get_queue, save_queue, get_branch, save_branch,
        get_categories, get_users, VER, today_iso, today_mmdd, gen_id
    )
    test("shared_data imports", True, f"Version {VER}")
except Exception as e:
    test("shared_data imports", False, str(e))
    print("\n🛑 FATAL: Cannot import shared_data.py. Fix this first.")
    sys.exit(1)

# ── TEST 2: Data directory ──
print("\n▶ 2. DATA DIRECTORY")
test("DATA_DIR exists", DATA_DIR.exists(), str(DATA_DIR))
test("DATA_DIR is writable", os.access(str(DATA_DIR), os.W_OK))
test("DATA_DIR is absolute", DATA_DIR.is_absolute(), str(DATA_DIR))

# ── TEST 3: File creation and reading ──
print("\n▶ 3. FILE I/O")
branch = get_branch()
test("branch.json readable", isinstance(branch, dict), f"keys={list(branch.keys())[:5]}")
test("branch has name", bool(branch.get("name")), branch.get("name","MISSING"))
test("branch has announcement field", "announcement" in branch)

cats = get_categories()
test("categories.json readable", isinstance(cats, list), f"{len(cats)} categories")
test("categories have services", all("services" in c for c in cats))

users = get_users()
test("users.json readable", isinstance(users, list), f"{len(users)} users")

queue = get_queue()
test("queue file readable", isinstance(queue, dict), f"keys={list(queue.keys())}")
test("queue has 'res' array", isinstance(queue.get("res"), list))
test("queue has 'oStat'", "oStat" in queue, f"value={queue.get('oStat')}")
test("queue has 'bqmsState'", "bqmsState" in queue)

# ── TEST 4: Write + Read cycle ──
print("\n▶ 4. WRITE → READ CYCLE")
# Write a test entry
test_entry = {
    "id": "DIAG_TEST_001", "slot": 999, "resNum": "DIAG-001",
    "lastName": "DIAGNOSTIC", "firstName": "TEST",
    "mi": "X", "mobile": "09990001111",
    "service": "Test", "serviceId": "test",
    "category": "Test", "categoryId": "test",
    "catIcon": "🧪", "priority": "regular",
    "status": "RESERVED", "bqmsNumber": None,
    "source": "ONLINE", "issuedAt": "2026-02-14T00:00:00",
    "arrivedAt": None, "completedAt": None,
}
queue["res"].append(test_entry)
save_queue(queue)

# Read back
queue2 = get_queue()
found = any(r.get("id") == "DIAG_TEST_001" for r in queue2.get("res", []))
test("Write → Read reservation", found,
     f"wrote 1 entry, read back {len(queue2.get('res',[]))} entries")

# Test oStat write
queue2["oStat"] = "intermittent"
save_queue(queue2)
queue3 = get_queue()
test("Write → Read oStat", queue3.get("oStat") == "intermittent",
     f"wrote 'intermittent', read back '{queue3.get('oStat')}'")

# Test announcement write
branch["announcement"] = "DIAGNOSTIC TEST MESSAGE"
save_branch(branch)
branch2 = get_branch()
test("Write → Read announcement", branch2.get("announcement") == "DIAGNOSTIC TEST MESSAGE",
     f"read back: '{branch2.get('announcement')}'")

# Test BQMS state write
queue3["bqmsState"] = {"loans": {"nowServing": "L-099"}}
save_queue(queue3)
queue4 = get_queue()
ns = queue4.get("bqmsState", {}).get("loans", {}).get("nowServing", "")
test("Write → Read bqmsState", ns == "L-099", f"read back: '{ns}'")

# Verify reservation STILL exists after bqmsState write
still_found = any(r.get("id") == "DIAG_TEST_001" for r in queue4.get("res", []))
test("Reservation survived bqmsState write", still_found,
     f"{len(queue4.get('res',[]))} entries after bqmsState update")

# ── TEST 5: Search simulation ──
print("\n▶ 5. TRACKER SEARCH SIMULATION")
q = get_queue()
res_list = q.get("res", [])

# Search by mobile
v = "09990001111"
found_mob = next((r for r in res_list
                  if r.get("mobile") == v and r.get("status") not in ("COMPLETED","NO_SHOW")),
                 None)
test("Search by mobile", found_mob is not None,
     f"searched '{v}', found={'yes' if found_mob else 'no'}")

# Search by Res# (simulating member tracker)
v2 = "DIAG-001"
found_rn = next((r for r in res_list
                 if r.get("resNum") == v2.strip().upper()
                 and r.get("status") not in ("COMPLETED","NO_SHOW")),
                None)
test("Search by Res#", found_rn is not None,
     f"searched '{v2}', found={'yes' if found_rn else 'no'}")

# ── TEST 6: Assign BQMS and verify ──
print("\n▶ 6. BQMS ASSIGNMENT SIMULATION")
fresh = get_queue()
for r in fresh["res"]:
    if r["id"] == "DIAG_TEST_001":
        r["bqmsNumber"] = "L-DIAG"
        r["status"] = "ARRIVED"
save_queue(fresh)

q2 = get_queue()
diag_entry = next((r for r in q2["res"] if r["id"] == "DIAG_TEST_001"), None)
test("BQMS assigned", diag_entry and diag_entry.get("bqmsNumber") == "L-DIAG",
     f"bqmsNumber={diag_entry.get('bqmsNumber') if diag_entry else 'ENTRY GONE!'}")
test("Status updated to ARRIVED", diag_entry and diag_entry.get("status") == "ARRIVED",
     f"status={diag_entry.get('status') if diag_entry else 'ENTRY GONE!'}")

# ── TEST 7: streamlit-autorefresh ──
print("\n▶ 7. DEPENDENCIES")
try:
    from streamlit_autorefresh import st_autorefresh
    test("streamlit-autorefresh installed", True)
except ImportError:
    test("streamlit-autorefresh installed", False,
         "RUN: pip install streamlit-autorefresh")

try:
    import streamlit
    test("streamlit installed", True, f"v{streamlit.__version__}")
except ImportError:
    test("streamlit installed", False)

# ── TEST 8: Cross-portal path verification ──
print("\n▶ 8. CROSS-PORTAL PATH CHECK")
import importlib
shared_spec = importlib.util.find_spec("shared_data")
if shared_spec:
    test("shared_data location", True, shared_spec.origin)
else:
    test("shared_data location", False, "NOT FOUND on sys.path!")

# Verify actual file paths
from shared_data import BRANCH_FILE, CATS_FILE, USERS_FILE, _queue_file
qf = _queue_file()
test("Queue file path", True, str(qf))
test("Queue file exists", qf.exists(), str(qf))
test("Branch file exists", BRANCH_FILE.exists(), str(BRANCH_FILE))

# ── CLEANUP ──
print("\n▶ CLEANUP")
# Remove diagnostic entry
final_q = get_queue()
final_q["res"] = [r for r in final_q["res"] if r.get("id") != "DIAG_TEST_001"]
final_q["oStat"] = "online"
final_q["bqmsState"] = {}
save_queue(final_q)

branch_clean = get_branch()
branch_clean["announcement"] = ""
save_branch(branch_clean)
test("Diagnostic data cleaned up", True)

# ── SUMMARY ──
print()
print("═══════════════════════════════════════════════════")
passed = sum(1 for _, p in results if p)
failed = sum(1 for _, p in results if not p)
total = len(results)
if failed == 0:
    print(f"  ✅ ALL {total} TESTS PASSED — Data layer is connected!")
else:
    print(f"  ❌ {failed} of {total} tests FAILED!")
    for name, p in results:
        if not p:
            print(f"     • {name}")
print("═══════════════════════════════════════════════════")
print()
print("📂 Data directory:", str(DATA_DIR))
print("📄 Queue file:   ", str(qf))
print("📄 Branch file:  ", str(BRANCH_FILE))
print()
print("If all tests pass but portals still seem disconnected:")
print("  1. Make sure ALL 3 .py files are in the SAME folder")
print("  2. Run BOTH portals from that folder:")
print("     streamlit run member_portal.py --server.port 8501")
print("     streamlit run staff_portal.py --server.port 8502")
print("  3. Install auto-refresh: pip install streamlit-autorefresh")
print("  4. Staff portal auto-refreshes every 15s now")
print("  5. Check the diagnostic footer at bottom of each portal")
