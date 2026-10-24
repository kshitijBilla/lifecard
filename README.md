# LifeCard (PS-40)

**Consent-Based Emergency Patient Record Bridge**  
*Hackathon Demo Prototype &bull; Zero Login / Signup &bull; Fictional Synthetic Data Only*

---

## Overview

LifeCard bridges the critical gap between a bystander at an accident scene, an emergency response doctor, and the patient's family:
- **Cardholder (Asha Sharma):** Holds a digital/physical NFC & QR card. Has granular real-time consent toggles (phone, address, blood group, alert chips) that instantly update what strangers see.
- **Stranger / Helper:** Scans the card with any phone camera without downloading an app or logging in. Gets an immediate "Call ambulance 112" dialer, consent-approved emergency info, and a one-tap button to share live GPS coordinates with the family.
- **Emergency Doctor (Dr. Meera Rao):** Upon arrival at City General Hospital, selects an audited clinical justification to unlock complete medical records (allergies, diabetes history, medications) with a 30-minute auto-expiring grant and broadcasts reassurance updates to the family.
- **Family (Rohan Sharma):** Monitors real-time alerts, tracks the emergency journey through a 4-step progress tracker, and views the patient's location on an embedded live map.

---

## Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate flat illustrated avatars
python tools/make_avatars.py

# 3. Run the automated test suite (all 43 checks)
python tests/smoke_test.py

# 4. Start local development server
python app.py
# Open http://localhost:5000 in your browser
```

For public HTTPS access on mobile devices (required for phone camera scanning and GPS geolocation sharing):
```bash
# Run Cloudflare quick tunnel (zero config, no account needed)
cloudflared tunnel --url http://localhost:5000
# or: ngrok http 5000
```

---

## 4-Phone / Multi-Device Demo Script

1. **Device 1 (Patient - Asha Sharma):**
   - Open `/enter/patient` (or click "Asha Sharma" on the home page).
   - View the 3D interactive flip card (click to flip front/back).
   - Switch to the **Privacy** tab: toggle "Share Blood Group" or "Share Medical Alerts" and watch the live iframe preview update instantly!
   - Tap "Issue a new card" to demonstrate instant rotation and revocation of old QR codes.

2. **Device 2 (Family - Rohan Sharma):**
   - Open `/enter/family` (or click "Rohan Sharma" on home page).
   - Keep this screen visible: the journey tracker starts at step 0 ("All Clear"), and the feed auto-polls every 3 seconds.

3. **Device 3 (Stranger / Bystander):**
   - Open `/s/asha-demo-token` (or scan the card QR with phone camera).
   - Helper screen displays the high-contrast "Call ambulance 112" button, the emergency contact, and medical alert chips.
   - Tap **"Share My Location with Family"**: GPS coordinates are sent to the family dashboard.
   - Notice Device 2 (Family) immediately triggers an audio/visual toast alert, highlights Step 2 ("Location Shared"), and centers the live map on the bystander's pin.

4. **Device 4 (Emergency Doctor - Dr. Meera Rao):**
   - Open `/enter/doctor` (or click "Dr. Meera Rao" on home page).
   - Use the camera scanner or click **"Simulate Scan"** to open `/s/<token>`.
   - As a verified doctor, Dr. Rao sees the **Confirm Arrival** screen with clinical justification selection (e.g., "Emergency treatment").
   - Click "Confirm Arrival & Unlock Medical Record":
     - Unlocks full clinical history (critical red allergy banner: Penicillin anaphylaxis, diabetes conditions, active medications table).
     - Starts a sticky **30-minute countdown grant**.
     - Device 2 (Family) advances to Step 3 ("Reached Hospital") with a notification that Asha reached City General Hospital.
   - In the **Notes** tab: click a preset chip (*"Asha is stable and being assessed"*) and tap "Send Update to Family Dashboard".
   - Device 2 (Family) updates Step 4 ("Doctor Update") with the reassurance message.
   - Doctor taps "End Access" to securely lock the record.

> [!TIP]
> **Safety Net Console:** If presenting on stage without multiple phones or in poor cellular GPS conditions, navigate to the **Presenter Console** at `/demo` (linked in the footer). Click the numbered simulation buttons (1. Scan &rarr; 2. Location &rarr; 3. Hospital &rarr; 4. Update) to trigger the entire pipeline with one click!

---

## Routes & Endpoints

| Route | Role / Scope | Description |
|---|---|---|
| `GET /` | Public | Role selector landing page with 3 persona cards and stranger test callout |
| `GET /enter/<role>` | Public | Sets session role (`patient`, `doctor`, `family`) and redirects |
| `GET /switch` | Public | Clears session role and returns to role selector |
| `GET /s/<token>` | Bystander / Doctor | The One Link: helper emergency page for strangers, confirm screen for doctors |
| `POST /s/<token>/location` | Bystander | Receives helper GPS coordinates `{event_id, lat, lng}` |
| `GET /patient` | Patient | Cardholder portal: 3D flip card, instant consent toggles, audit feed, family |
| `POST /patient/reissue` | Patient | Rotates card token, permanently revoking previous QR |
| `POST /api/consent` | Patient | Asynchronous instant update for granular privacy toggles |
| `GET /doctor` | Doctor | Station dashboard with BarcodeDetector camera scanner and recent accesses |
| `POST /doctor/open/<token>` | Doctor | Confirms hospital arrival, logs record access, grants 30-min window |
| `GET /doctor/record` | Doctor | Full clinical chart (allergies, vitals, medications, history, notes) |
| `POST /doctor/note` | Doctor | Appends clinical assessment note to patient audit trail |
| `POST /doctor/update` | Doctor | Broadcasts triage status reassurance update to family feed |
| `POST /doctor/end` | Doctor | Immediately terminates emergency clinical session and locks records |
| `GET /family` | Family | Real-time monitoring feed, 4-step journey tracker, live embedded Google map |
| `GET /api/feed` | Family / Patient | JSON polling endpoint (polled every 3-4s with change detection) |
| `GET /card.png` | Public / Patient | High-resolution 1012x638 Pillow render for physical wallet printing |
| `GET /qr.png` | Public | Dynamic QR code generator pointing to current active token |
| `GET /demo` | Presenter | Stage console with one-click sequential simulation actions and DB reset |
| `POST /demo/<action>` | Presenter | Executes simulation action (`scan`, `location`, `hospital`, `update`, `reset`) |

---

## Honest Limitations (For Judges & Evaluators)

1. **NFC Simulation:** Physical NFC cards encode and broadcast the exact same URL (`/s/<token>`) as the QR code. Tapping an NFC tag with an Android or iPhone opens the browser to that URL directly.
2. **Alert Delivery:** Alerts are demonstrated via live in-app polling (every 3 seconds), vibration (`navigator.vibrate`), and browser Notification APIs. In production, webhooks would trigger SMS via Twilio or WhatsApp Business API.
3. **Doctor Verification:** Doctor identity in this prototype is simulated via the role picker. A production deployment would integrate the National Medical Commission (NMC) DigiDoctor registry and ABHA (Ayushman Bharat Health Account) tokens.
4. **Data Ephemerality:** All data is stored in SQLite (`lifecard.db` or `/tmp/lifecard.db`). Cloud instances reset to the clean default seed upon redeployment.
5. **Fictional Data:** All personas, hospitals (City General Hospital), doctors, addresses, and phone numbers are completely fictional synthetic data.
