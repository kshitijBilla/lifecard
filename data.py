"""Hard-coded, realistic fictional demo data for LifeCard (hackathon PS-40).

All data belongs to the fictional patient persona Asha Sharma and City General Hospital.
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
    "address": "B-12, Sector 21, Gurugram, Haryana",
    "avatar": "asha.png",
    "organ_donor": True,
    "primary_physician": "Dr. Anil Iyer (Apex Clinic, Gurugram - +91 98111 22334)",
    "emergency_name": "Rohan Sharma",
    "emergency_relation": "Brother",
    "emergency_phone": "+91 98100 00002",
    "emergency_contact": {
        "name": "Rohan Sharma",
        "relation": "brother",
        "phone": "+91 98100 00002",
    },
    # Scannable alert chips
    "alert_chips": [
        "Diabetic (Type 2)",
        "Asthma (Exercise-induced)",
        "Severe Penicillin Allergy",
    ],
    "allergies": [
        {
            "name": "Penicillin",
            "substance": "Penicillin & Beta-lactams",
            "severity": "Severe",
            "reaction": "Anaphylaxis, Angioedema & Severe Bronchospasm",
            "critical": True,
        },
        {
            "name": "Peanuts",
            "substance": "Peanuts & Tree Nuts",
            "severity": "Moderate",
            "reaction": "Urticaria, Facial Flushing & Hives",
            "critical": False,
        },
        {
            "name": "Sulfa Drugs",
            "substance": "Sulfonamides",
            "severity": "Mild",
            "reaction": "Maculopapular Skin Rash",
            "critical": False,
        },
    ],
    "conditions": [
        {
            "name": "Type 2 Diabetes Mellitus",
            "since": "2019",
            "status": "Managed & Stable",
            "detail": "HbA1c 7.2% (Aug 2026). Controlled with Metformin 500mg BD and dietary regulation.",
        },
        {
            "name": "Mild Bronchial Asthma",
            "since": "2016",
            "status": "Intermittent / Controlled",
            "detail": "Exercise-induced bronchospasm. Salbutamol 100mcg reliever inhaler as needed; no steroid maintenance required.",
        },
        {
            "name": "Seasonal Allergic Rhinitis",
            "since": "2021",
            "status": "Mild Seasonal",
            "detail": "Pollen & dust hypersensitivity during spring/autumn. Managed with Cetirizine PRN.",
        },
    ],
    "medications": [
        {
            "name": "Metformin Hydrochloride",
            "dose": "500 mg",
            "frequency": "Twice daily (BD)",
            "route": "Oral",
            "timing": "With morning and evening meals",
            "purpose": "Glycemic control (Type 2 Diabetes)",
            "prescribed_by": "Dr. Anil Iyer",
        },
        {
            "name": "Salbutamol Inhaler (Ventolin)",
            "dose": "100 mcg / actuation",
            "frequency": "As needed (PRN)",
            "route": "Inhalation",
            "timing": "1-2 puffs prior to exercise or during wheeze",
            "purpose": "Fast-acting bronchodilator for asthma",
            "prescribed_by": "Dr. Anil Iyer",
        },
        {
            "name": "Vitamin D3 (Cholecalciferol)",
            "dose": "60,000 IU",
            "frequency": "Once weekly",
            "route": "Oral",
            "timing": "Sunday mornings with milk",
            "purpose": "Correction of Vitamin D deficiency",
            "prescribed_by": "Dr. Anil Iyer",
        },
        {
            "name": "Cetirizine Hydrochloride",
            "dose": "10 mg",
            "frequency": "As needed (PRN)",
            "route": "Oral",
            "timing": "At bedtime during seasonal flare-ups",
            "purpose": "Antihistamine for allergic rhinitis",
            "prescribed_by": "Dr. Anil Iyer",
        },
    ],
    "vitals": [
        {"label": "Blood pressure", "value": "118/76", "unit": "mmHg", "status": "Normal", "icon": "heart"},
        {"label": "Heart pulse", "value": "72", "unit": "bpm", "status": "Normal Sinus", "icon": "pulse"},
        {"label": "Fasting glucose", "value": "104", "unit": "mg/dL", "status": "Good Control", "icon": "drop"},
        {"label": "Oxygen (SpO2)", "value": "99", "unit": "%", "status": "Room Air", "icon": "wind"},
        {"label": "Body temp", "value": "98.4", "unit": "°F", "status": "Afebrile", "icon": "thermometer"},
        {"label": "Body weight", "value": "62", "unit": "kg", "status": "BMI 22.8", "icon": "scale"},
    ],
    "labs": [
        {"test": "Glycated Hemoglobin (HbA1c)", "result": "7.2%", "reference": "< 5.7% (Diabetic target < 7.5%)", "date": "18 Aug 2026", "status": "Optimal Control"},
        {"test": "Serum Creatinine", "result": "0.8 mg/dL", "reference": "0.6 - 1.1 mg/dL", "date": "18 Aug 2026", "status": "Normal Kidney Function"},
        {"test": "Total Cholesterol", "result": "182 mg/dL", "reference": "< 200 mg/dL", "date": "18 Aug 2026", "status": "Normal"},
        {"test": "HDL Good Cholesterol", "result": "52 mg/dL", "reference": "> 50 mg/dL", "date": "18 Aug 2026", "status": "Optimal"},
        {"test": "LDL Cholesterol", "result": "102 mg/dL", "reference": "< 100 mg/dL", "date": "18 Aug 2026", "status": "Near Optimal"},
        {"test": "Hemoglobin (CBC)", "result": "13.2 g/dL", "reference": "12.0 - 15.5 g/dL", "date": "18 Aug 2026", "status": "Normal"},
        {"test": "Platelet Count", "result": "240,000 /µL", "reference": "150,000 - 450,000 /µL", "date": "18 Aug 2026", "status": "Normal"},
    ],
    "history": [
        {
            "date": "Aug 2026",
            "title": "Comprehensive Diabetic Panel",
            "category": "Diagnostics",
            "detail": "HbA1c 7.2%, serum creatinine 0.8 mg/dL, urine microalbumin negative, normal lipid profile. Retinal screening clear.",
        },
        {
            "date": "Mar 2026",
            "title": "Pulmonary Asthma Function Review",
            "category": "Review",
            "detail": "Peak Expiratory Flow Rate (PEFR) 420 L/min (92% of predicted). Spirometry FEV1/FVC 82%. Lungs clear bilaterally.",
        },
        {
            "date": "Nov 2025",
            "title": "Quadrivalent Influenza Immunization",
            "category": "Vaccine",
            "detail": "Annual seasonal influenza immunization administered intramuscularly (left deltoid). No adverse reaction.",
        },
        {
            "date": "Jun 2023",
            "title": "Laparoscopic Appendectomy",
            "category": "Surgery",
            "detail": "Uncomplicated minimally invasive appendix removal at Medanta Gurugram. Discharged on post-op day 2 with complete recovery.",
        },
        {
            "date": "Jan 2019",
            "title": "Type 2 Diabetes Mellitus Diagnosis",
            "category": "Chronic",
            "detail": "Initial presentation with polydipsia and mild fatigue. Fasting plasma glucose 162 mg/dL. Initiated Metformin 500mg twice daily with medical nutrition therapy.",
        },
    ],
    "surgeries": [
        {"procedure": "Laparoscopic Appendectomy", "hospital": "Medanta Hospital, Gurugram", "date": "12 Jun 2023", "surgeon": "Dr. S. K. Mittal", "outcome": "Successful, healed with no complications"},
        {"procedure": "Left Wrist Diagnostic Arthroscopy", "hospital": "Fortis Memorial, Gurugram", "date": "04 Oct 2020", "surgeon": "Dr. R. Sengupta", "outcome": "Minor TFCC sprain treated conservatively"},
    ],
    "family_history": [
        {"relation": "Father", "condition": "Essential Hypertension (diagnosed age 52, well controlled)"},
        {"relation": "Mother", "condition": "Type 2 Diabetes Mellitus (diagnosed age 56, on oral hypoglycemics)"},
        {"relation": "Brother (Rohan)", "condition": "No known chronic illnesses or drug allergies"},
    ],
    "insurance": {
        "provider": "Care Health Elite Insurance",
        "policy": "CHI-2024-88921A",
        "policy_no": "CHI-2024-88921A",
        "plan": "Comprehensive Health Floater - ₹10 Lakh",
        "valid_to": "31 Dec 2027",
        "tpa_phone": "+91 1800 200 4488",
        "pre_auth_code": "CGH-EMERG-AUTH-2026",
    },
}

DOCTOR = {
    "name": "Dr. Meera Rao",
    "speciality": "Emergency Medicine",
    "specialty": "Emergency Medicine",
    "reg_no": "DMC-84291 / GGM-EM-2014",
    "avatar": "drrao.png",
    "hospital": "City General Hospital",
    "hospital_address": "Sector 44, Gurugram, Haryana",
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
        "role_label": "Primary Emergency Contact",
        "note": "Lives 4 km away in Sector 14, Gurugram. First emergency contact.",
    },
    {
        "name": "Kavita Sharma",
        "relation": "Mother",
        "phone": "+91 98100 00003",
        "avatar": "kavita.png",
        "primary": False,
        "role_label": "Secondary Family Contact",
        "note": "Secondary contact. Notified immediately after Rohan.",
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
    "Asha is stable, conscious, and resting comfortably in the emergency observation unit.",
    "Emergency lab panel & vitals checked: blood sugar and oxygen are well-controlled.",
    "Attending physician Dr. Meera Rao has initiated preliminary observation; family may visit.",
    "Patient is responding well to treatment and preparing for transfer to room.",
]
DOCTOR_PRESET_UPDATES = QUICK_UPDATES

# Stage safety net spots
DEMO_SPOTS = [
    {"place": "MG Road Metro Station, Gurugram", "name": "MG Road Metro Station", "lat": 28.4800, "lng": 77.0800},
    {"place": "Cyber Hub, DLF Phase 2, Gurugram", "name": "Cyber Hub, Gurugram", "lat": 28.4950, "lng": 77.0890},
    {"place": "Sector 29 Commercial Market, Gurugram", "name": "Sector 29 Market", "lat": 28.4686, "lng": 77.0644},
]
DEMO_LOCATIONS = DEMO_SPOTS

GRANT_MINUTES = 30
SCAN_DEDUPE_SECONDS = 45
HOSPITAL_SCAN_COOLDOWN_SECONDS = 3600

TRANSLATIONS_EN = STRINGS["en"]
TRANSLATIONS_HI = STRINGS["hi"]
