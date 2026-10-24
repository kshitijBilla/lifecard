"""End-to-end smoke test suite for LifeCard PS-40.

Tests:
1. Role entry & navigation
2. Helper page privacy toggles
3. Scan deduplication within 45 seconds
4. Location validation
5. Doctor confirm -> record access grant
6. 30-minute expiry
7. Doctor end access early
8. Family feed ordering & journey tracker
9. Card reissue rotates token and revokes old QR
10. Open redirect protection
"""

import os
import sys
import tempfile
from datetime import timedelta

# Set temporary database path for tests
tmp_dir = tempfile.mkdtemp()
os.environ["DB_PATH"] = os.path.join(tmp_dir, "test_lifecard.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as A

app = A.app
app.config["TESTING"] = True

passed = []


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"{status} - {name}")
    if not condition:
        sys.exit(1)
    passed.append(name)


def main():
    with app.app_context():
        A.init_db()

    client = app.test_client()

    # -------------------------------------------------------------------------
    # 1. Role Entry & Switching
    # -------------------------------------------------------------------------
    r = client.get("/enter/patient")
    check("Role entry: /enter/patient redirects to /patient", r.status_code == 302 and r.headers["Location"].endswith("/patient"))
    with client.session_transaction() as sess:
        check("Role entry: session['role'] is patient", sess.get("role") == "patient")

    r = client.get("/enter/doctor")
    check("Role entry: /enter/doctor redirects to /doctor", r.status_code == 302 and r.headers["Location"].endswith("/doctor"))
    with client.session_transaction() as sess:
        check("Role entry: session['role'] is doctor", sess.get("role") == "doctor")

    r = client.get("/enter/family")
    check("Role entry: /enter/family redirects to /family", r.status_code == 302 and r.headers["Location"].endswith("/family"))
    with client.session_transaction() as sess:
        check("Role entry: session['role'] is family", sess.get("role") == "family")

    client.get("/switch")
    with client.session_transaction() as sess:
        check("Role switch: /switch clears session['role']", sess.get("role") is None)

    # -------------------------------------------------------------------------
    # 2. Helper Page Privacy Toggles
    # -------------------------------------------------------------------------
    with app.app_context():
        token = A.get_current_token()

    # Reset consents to all 1
    client.post("/api/consent", json={"share_phone": 1, "share_address": 1, "share_blood": 1, "share_alerts": 1})
    r = client.get(f"/s/{token}?preview=1")
    html = r.get_data(as_text=True)
    check("Helper page shows phone when consented", "+91 98100 00001" in html)
    check("Helper page shows address when consented", "Sector 21" in html)
    check("Helper page shows blood group when consented", "B+" in html)
    check("Helper page shows alert chips when consented", "Diabetic" in html and "Asthma" in html)

    # Turn all off
    client.post("/api/consent", json={"share_phone": 0, "share_address": 0, "share_blood": 0, "share_alerts": 0})
    r = client.get(f"/s/{token}?preview=1")
    html = r.get_data(as_text=True)
    check("Helper page hides phone when disabled", "+91 98100 00001" not in html)
    check("Helper page hides address when disabled", "Sector 21" not in html)
    check("Helper page hides blood group when disabled", "B+" not in html)
    check("Helper page hides alert chips when disabled", "Diabetic" not in html and "Asthma" not in html)

    # Restore consents
    client.post("/api/consent", json={"share_phone": 1, "share_address": 1, "share_blood": 1, "share_alerts": 1})

    # -------------------------------------------------------------------------
    # 3. Scan Deduplication Within 45 Seconds
    # -------------------------------------------------------------------------
    with app.app_context():
        A.get_db().execute("DELETE FROM events")
        A.get_db().commit()

    # First stranger scan
    stranger = app.test_client()
    r1 = stranger.get(f"/s/{token}")
    check("Stranger scan returns 200", r1.status_code == 200)

    with app.app_context():
        count1 = A.get_db().execute("SELECT COUNT(*) FROM events WHERE kind='helper_scan'").fetchone()[0]
    check("First scan creates 1 helper_scan event", count1 == 1)

    # Second scan immediately after (within 45s)
    r2 = stranger.get(f"/s/{token}")
    check("Immediate second scan returns 200", r2.status_code == 200)

    with app.app_context():
        count2 = A.get_db().execute("SELECT COUNT(*) FROM events WHERE kind='helper_scan'").fetchone()[0]
    check("Scan within 45s is deduplicated (count remains 1)", count2 == 1)

    # -------------------------------------------------------------------------
    # 4. Location Validation
    # -------------------------------------------------------------------------
    with app.app_context():
        ev = A.get_db().execute("SELECT id FROM events WHERE kind='helper_scan' LIMIT 1").fetchone()
        ev_id = ev["id"]

    # Valid location
    r_loc = stranger.post(f"/s/{token}/location", json={"event_id": ev_id, "lat": 28.4595, "lng": 77.0266})
    check("Valid coordinates accepted (200 ok)", r_loc.status_code == 200 and r_loc.get_json()["ok"] is True)

    # Invalid latitude
    r_bad = stranger.post(f"/s/{token}/location", json={"event_id": ev_id, "lat": 999.0, "lng": 77.0266})
    check("Out-of-range latitude rejected (400)", r_bad.status_code == 400)

    # Expired / fake event ID
    r_fake = stranger.post(f"/s/{token}/location", json={"event_id": 99999, "lat": 28.45, "lng": 77.02})
    check("Non-existent event ID rejected (404)", r_fake.status_code == 404)

    # -------------------------------------------------------------------------
    # 5. Doctor Confirm -> Record Access Grant
    # -------------------------------------------------------------------------
    doc = app.test_client()
    doc.get("/enter/doctor")  # Establish doctor role

    # Opening /s/<token> as doctor opens confirm screen
    r_doc_scan = doc.get(f"/s/{token}")
    check("Doctor scanning card sees confirm screen", b"Confirm Arrival" in r_doc_scan.data)

    # Submitting with invalid reason rejected
    r_bad_reason = doc.post(f"/doctor/open/{token}", data={"reason": "InvalidReason"})
    check("Doctor invalid reason rejected with redirect", r_bad_reason.status_code == 302 and "/doctor/record" not in r_bad_reason.headers["Location"])

    # Submitting with valid reason grants access
    r_grant = doc.post(f"/doctor/open/{token}", data={"reason": "Emergency treatment"}, follow_redirects=True)
    check("Doctor valid reason opens /doctor/record", r_grant.status_code == 200 and b"CRITICAL ALLERGY ALERT" in r_grant.data)
    check("Record shows medications and vitals", b"Metformin" in r_grant.data and b"118/76" in r_grant.data)

    # Check hospital scan was logged
    with app.app_context():
        hosp_ev = A.get_db().execute("SELECT * FROM events WHERE kind='hospital_scan'").fetchone()
    check("Hospital scan logged with City General Hospital", hosp_ev is not None and "City General Hospital" in hosp_ev["text"])

    # -------------------------------------------------------------------------
    # 6. 30-Minute Expiry
    # -------------------------------------------------------------------------
    with app.app_context():
        # Age the record_access event by 31 minutes
        old_time = A.utc_ts(A.utc_now() - timedelta(minutes=31))
        A.get_db().execute("UPDATE events SET created_at=? WHERE kind='record_access'", (old_time,))
        A.get_db().commit()

    r_expired = doc.get("/doctor/record", follow_redirects=False)
    check("Access expires after 30 minutes (redirects to /doctor)", r_expired.status_code == 302 and r_expired.headers["Location"].endswith("/doctor"))

    # -------------------------------------------------------------------------
    # 7. Doctor End Access Early
    # -------------------------------------------------------------------------
    # Re-open access
    doc.post(f"/doctor/open/{token}", data={"reason": "Admission / triage"})
    check("Fresh doctor access works", doc.get("/doctor/record").status_code == 200)

    # Doctor ends access
    r_end = doc.post("/doctor/end", follow_redirects=False)
    check("Doctor end access redirects to /doctor", r_end.status_code == 302 and r_end.headers["Location"].endswith("/doctor"))

    # Attempting to re-open record without new scan is blocked
    r_locked = doc.get("/doctor/record", follow_redirects=False)
    check("Record locked immediately after access ended", r_locked.status_code == 302 and r_locked.headers["Location"].endswith("/doctor"))

    # -------------------------------------------------------------------------
    # 8. Family Feed Ordering & Journey Tracker
    # -------------------------------------------------------------------------
    fam = app.test_client()
    fam.get("/enter/family")
    r_feed = fam.get("/api/feed?scope=family")
    check("Family feed returns 200 JSON", r_feed.status_code == 200)
    feed_data = r_feed.get_json()
    events = feed_data["events"]
    check("Family feed has events", len(events) > 0)
    # Check descending order by ID
    is_desc = all(events[i]["id"] >= events[i + 1]["id"] for i in range(len(events) - 1))
    check("Family feed is in descending order (newest first)", is_desc)
    check("Family journey tracker state exists", "journey" in feed_data and "current" in feed_data["journey"])

    # -------------------------------------------------------------------------
    # 9. Card Reissue Kills Old Token
    # -------------------------------------------------------------------------
    patient = app.test_client()
    patient.get("/enter/patient")
    r_reissue = patient.post("/patient/reissue", follow_redirects=True)
    check("Card reissue redirects to /patient", r_reissue.status_code == 200)

    # Old token is now dead
    r_dead = app.test_client().get(f"/s/{token}")
    check("Old QR token returns 404 (Card Revoked)", r_dead.status_code == 404 and b"This LifeCard is No Longer Active" in r_dead.data)

    # New token works
    with app.app_context():
        new_tok = A.get_current_token()
    check("New token is different from old token", new_tok != token)
    r_new = app.test_client().get(f"/s/{new_tok}?preview=1")
    check("New token resolves with 200 OK", r_new.status_code == 200)

    # -------------------------------------------------------------------------
    # 10. Open Redirect Blocked
    # -------------------------------------------------------------------------
    r_evil1 = client.get("/enter/patient?next=https://evil.com")
    check("Open redirect with https://evil.com blocked", not r_evil1.headers["Location"].startswith("https://evil.com"))

    r_evil2 = client.get("/enter/patient?next=//evil.com")
    check("Open redirect with //evil.com blocked", not r_evil2.headers["Location"].startswith("//evil.com"))

    r_evil3 = client.get("/enter/patient?next=\\\\evil.com")
    check("Open redirect with \\\\evil.com blocked", not r_evil3.headers["Location"].startswith("\\"))

    r_valid_next = client.get("/enter/patient?next=/family")
    check("Safe relative next path /family allowed", r_valid_next.headers["Location"].endswith("/family"))

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print(f"\n==========================================")
    print(f"All {len(passed)} smoke tests passed successfully!")
    print(f"==========================================\n")


if __name__ == "__main__":
    main()
