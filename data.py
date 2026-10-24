"""Hard-coded, entirely fictional demo data for LifeCard (hackathon PS-40).

Nothing here is a real person, hospital, policy or phone number.
"""

from i18n import STRINGS

PATIENT = {
    "name": "Asha Sharma",
    "sex": "F",
    "sex_long": "Female",
    "dob": "1992-04-18",
    "age": 34,
    "blood": "B+",
    "blood_group": "B+",
    "phone": "+91 98100 00001",
    "address": "B-12, Sector 21, Gurugram",
    "avatar": "asha.png",
    "organ_donor": True,
    "primary_physician": "Dr. Anil Iyer",
    "emergency_name": "Rohan Sharma",
    "emergency_relation": "Brother",
    "emergency_phone": "+91 98100 00002",
    "emergency_contact": {
        "name": "Rohan Sharma",
        "relation": "brother",
        "phone": "+91 98100 00002",
    },
    # Short, scannable chips a bystander or medic reads first.
    "alert_chips": ["Diabetic", "Asthma", "Allergic to penicillin"],
    "allergies": [
        {"name": "Penicillin", "substance": "Penicillin", "severity": "Severe", "reaction": "Anaphylaxis"},
        {"name": "Peanuts", "substance": "Peanuts", "severity": "Moderate", "reaction": "Hives"},
    ],
    "conditions": [
        {
            "name": "Type 2 diabetes",
            "since": "2019",
            "detail": "HbA1c 7.2% (Aug 2026). Diet and metformin controlled.",
        },
        {
            "name": "Mild asthma",
            "since": "2016",
            "detail": "Exercise induced. Reliever inhaler as needed, no ICS.",
        },
    ],
    "medications": [
        {"name": "Metformin", "dose": "500 mg", "freq": "Twice daily", "frequency": "Twice daily", "route": "Oral", "purpose": "Type 2 diabetes control", "note": "After meals"},
        {"name": "Salbutamol inhaler", "dose": "100 mcg", "freq": "As needed", "frequency": "As needed", "route": "Inhalation", "purpose": "Asthma reliever", "note": "2 puffs for wheeze"},
        {"name": "Vitamin D3", "dose": "60,000 IU", "freq": "Weekly", "frequency": "Weekly", "route": "Oral", "purpose": "Deficiency management", "note": "Sunday morning"},
    ],
    "vitals": [
        {"label": "Blood pressure", "value": "118/76", "unit": "mmHg", "icon": "heart"},
        {"label": "Pulse", "value": "72", "unit": "bpm", "icon": "pulse"},
        {"label": "Fasting glucose", "value": "104", "unit": "mg/dL", "icon": "drop"},
        {"label": "Weight", "value": "62", "unit": "kg", "icon": "scale"},
    ],
    "vitals_dict": {
        "bp": "118/76 mmHg",
        "pulse": "72 bpm",
        "glucose": "104 mg/dL",
        "weight": "62 kg",
        "spo2": "99% on room air",
    },
    "history": [
        {"date": "Aug 2026", "title": "Lab panel", "detail": "HbA1c 7.2%, lipids normal, creatinine 0.8."},
        {"date": "Mar 2026", "title": "Asthma review", "detail": "Spirometry normal. Continue reliever only."},
        {"date": "Nov 2025", "title": "Influenza vaccine", "detail": "Seasonal quadrivalent, left deltoid."},
        {"date": "Jun 2023", "title": "Appendectomy", "detail": "Laparoscopic, uncomplicated. 2-day stay."},
        {"date": "Jan 2019", "title": "Type 2 diabetes diagnosed", "detail": "Started metformin 500 mg BD."},
    ],
    "insurance": {
        "provider": "Care Health Elite (demo)",
        "policy": "SHA-DEMO-4471-0092",
        "policy_no": "SHA-DEMO-4471-0092",
        "plan": "Family Floater - 5 Lakh",
        "valid_to": "31 Mar 2027",
        "tpa_phone": "+91 1800 200 4488",
    },
}

DOCTOR = {
    "name": "Dr. Meera Rao",
    "speciality": "Emergency Medicine",
    "specialty": "Emergency Medicine",
    "reg_no": "DEMO/GGM/2014/8821",
    "avatar": "drrao.png",
    "hospital": "City General Hospital",
    "hospital_address": "Sector 44, Gurugram",
    "lat": 28.4510,
    "lng": 77.0620,
}

FAMILY = [
    {
        "name": "Rohan Sharma",
        "relation": "Brother",
        "phone": "+91 98100 00002",
        "avatar": "rohan.png",
        "primary": True,
        "note": "Primary emergency contact. Lives 4 km away.",
    },
    {
        "name": "Kavita Sharma",
        "relation": "Mother",
        "phone": "+91 98100 00003",
        "avatar": "kavita.png",
        "primary": False,
        "note": "Secondary contact. Notified after Rohan.",
    },
]

FAMILY_VIEWER = FAMILY[0]
FAMILY_MEMBERS = FAMILY

ACCESS_REASONS = [
    ("emergency", "Emergency treatment"),
    ("triage", "Admission / triage"),
    ("routine", "Routine consultation"),
]
REASON_LABELS = dict(ACCESS_REASONS)
DOCTOR_REASONS = [r[1] for r in ACCESS_REASONS]

QUICK_UPDATES = [
    "Asha is stable and being assessed.",
    "Bloods and ECG done, results in 20 minutes.",
    "Moving to the observation ward, nothing to worry about.",
]
DOCTOR_PRESET_UPDATES = QUICK_UPDATES

# Stage safety net: fixed, plausible Gurugram coordinates for /demo.
DEMO_SPOTS = [
    {"place": "MG Road Metro, Gurugram", "name": "MG Road Metro, Gurugram", "lat": 28.4800, "lng": 77.0800},
    {"place": "Cyber Hub, Gurugram", "name": "Cyber Hub, Gurugram", "lat": 28.4950, "lng": 77.0890},
    {"place": "Sector 29 Market, Gurugram", "name": "Sector 29 Market, Gurugram", "lat": 28.4686, "lng": 77.0644},
]
DEMO_LOCATIONS = DEMO_SPOTS

GRANT_MINUTES = 30
SCAN_DEDUPE_SECONDS = 45
HOSPITAL_SCAN_COOLDOWN_SECONDS = 3600

TRANSLATIONS_EN = STRINGS["en"]
TRANSLATIONS_HI = STRINGS["hi"]
