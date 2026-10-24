"""LifeCard (PS-40: Consent-Based Emergency Patient Record Bridge).

Zero-login, role-picker demo prototype built with Flask, Jinja2, SQLite, and Pillow.
"""

import io
import math
import os
import random
import secrets
import sqlite3
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import qrcode
from flask import (Flask, abort, flash, g, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from PIL import Image, ImageDraw, ImageFont, ImageOps
from werkzeug.middleware.proxy_fix import ProxyFix

from data import (DEMO_LOCATIONS, DOCTOR, DOCTOR_PRESET_UPDATES,
                  DOCTOR_REASONS, FAMILY_MEMBERS, PATIENT,
                  TRANSLATIONS_EN, TRANSLATIONS_HI)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("VERCEL"):
    DB_PATH = os.environ.get("DB_PATH", "/tmp/lifecard.db")
else:
    DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "lifecard.db"))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

ACCESS_MINUTES = 30
SCAN_DEDUPE_SECONDS = 45
IST = timezone(timedelta(hours=5, minutes=30))

app = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPLATES_DIR)
app.secret_key = os.environ.get("SECRET_KEY", "lifecard-ps40-hackathon-2026-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# -----------------------------------------------------------------------------
# Database Setup & Helpers
# -----------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    token TEXT PRIMARY KEY,
    share_phone INTEGER NOT NULL DEFAULT 1,
    share_address INTEGER NOT NULL DEFAULT 1,
    share_blood INTEGER NOT NULL DEFAULT 1,
    share_alerts INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    reason TEXT,
    text TEXT,
    lat REAL,
    lng REAL,
    place TEXT,
    created_at TEXT NOT NULL
);
"""


def utc_now():
    return datetime.now(timezone.utc)


def utc_ts(dt=None):
    return (dt or utc_now()).strftime("%Y-%m-%d %H:%M:%S")


def parse_utc_ts(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return utc_now()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM settings")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO settings (token, share_phone, share_address, share_blood, share_alerts) "
            "VALUES ('asha-demo-token', 1, 1, 1, 1)"
        )
    conn.commit()
    conn.close()


def get_settings():
    row = get_db().execute("SELECT * FROM settings LIMIT 1").fetchone()
    if not row:
        get_db().execute(
            "INSERT INTO settings (token, share_phone, share_address, share_blood, share_alerts) "
            "VALUES ('asha-demo-token', 1, 1, 1, 1)"
        )
        get_db().commit()
        row = get_db().execute("SELECT * FROM settings LIMIT 1").fetchone()
    return row


def get_current_token():
    return get_settings()["token"]


def log_event(kind, text, reason=None, lat=None, lng=None, place=None):
    cur = get_db().execute(
        "INSERT INTO events (kind, reason, text, lat, lng, place, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (kind, reason, text, lat, lng, place, utc_ts()),
    )
    get_db().commit()
    return cur.lastrowid


# -----------------------------------------------------------------------------
# Jinja Filters & Context Processors
# -----------------------------------------------------------------------------

@app.template_filter("ist")
def ist_filter(s):
    dt = parse_utc_ts(s).astimezone(IST)
    return dt.strftime("%d %b %Y, %I:%M %p IST")


@app.template_filter("timeago")
def timeago_filter(s):
    dt = parse_utc_ts(s)
    diff = (utc_now() - dt).total_seconds()
    if diff < 5:
        return "just now"
    if diff < 60:
        return f"{int(diff)}s ago"
    if diff < 3600:
        return f"{int(diff // 60)} min ago"
    if diff < 86400:
        return f"{int(diff // 3600)} hr ago"
    return dt.astimezone(IST).strftime("%d %b")


def format_event_view(row):
    e = dict(row)
    kind = e["kind"]
    e["time_ist"] = ist_filter(e["created_at"])
    e["time_ago"] = timeago_filter(e["created_at"])

    icons = {
        "helper_scan": "📱",
        "hospital_scan": "🏥",
        "doctor_update": "📣",
        "record_access": "🔓",
        "access_ended": "🔒",
        "clinical_note": "📝",
    }
    titles = {
        "helper_scan": "Emergency QR Scanned",
        "hospital_scan": "Arrived at Hospital",
        "doctor_update": "Doctor Status Update",
        "record_access": "Medical Record Accessed",
        "access_ended": "Doctor Access Closed",
        "clinical_note": "Clinical Assessment Added",
    }
    e["icon"] = icons.get(kind, "📌")
    e["title"] = titles.get(kind, kind.replace("_", " ").title())

    if e.get("lat") and e.get("lng"):
        e["maps_url"] = f"https://www.google.com/maps/search/?api=1&query={e['lat']},{e['lng']}"
    else:
        e["maps_url"] = None

    return e


@app.context_processor
def inject_globals():
    return {
        "role": session.get("role"),
        "current_token": get_current_token(),
        "patient": PATIENT,
        "doctor": DOCTOR,
        "family_members": FAMILY_MEMBERS,
        "embed": request.args.get("embed") == "1",
    }


def safe_relative_redirect(target, fallback_endpoint="index"):
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target or ":" in target:
        return redirect(url_for(fallback_endpoint))
    return redirect(target)


def public_base():
    base = os.environ.get("BASE_URL", "").rstrip("/")
    if base:
        return base
    return request.url_root.rstrip("/")


def check_active_doctor_grant():
    """Checks if a valid doctor grant exists within the last 30 minutes without subsequent access_ended."""
    cutoff = utc_ts(utc_now() - timedelta(minutes=ACCESS_MINUTES))
    last_access = get_db().execute(
        "SELECT * FROM events WHERE kind='record_access' AND created_at >= ? "
        "ORDER BY id DESC LIMIT 1",
        (cutoff,),
    ).fetchone()

    if not last_access:
        return None

    # Check if access was terminated after this access
    ended = get_db().execute(
        "SELECT * FROM events WHERE kind='access_ended' AND id > ? "
        "ORDER BY id DESC LIMIT 1",
        (last_access["id"],),
    ).fetchone()

    if ended:
        return None

    access_time = parse_utc_ts(last_access["created_at"])
    elapsed = (utc_now() - access_time).total_seconds()
    remaining = max(0, int(ACCESS_MINUTES * 60 - elapsed))

    return {
        "event": last_access,
        "seconds_left": remaining,
        "minutes_left": max(1, math.ceil(remaining / 60)),
    }


# -----------------------------------------------------------------------------
# Public & Role Routes
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/enter/<role>")
def enter_role(role):
    if role not in ("patient", "doctor", "family"):
        abort(400, "Invalid role specified.")
    session["role"] = role
    nxt = request.args.get("next")
    if nxt:
        return safe_relative_redirect(nxt)
    role_endpoints = {
        "patient": "patient_home",
        "doctor": "doctor_home",
        "family": "family_home",
    }
    return redirect(url_for(role_endpoints[role]))


@app.route("/switch")
def switch_role():
    session.pop("role", None)
    return redirect(url_for("index"))


# -----------------------------------------------------------------------------
# The One QR/NFC Link: /s/<token>
# -----------------------------------------------------------------------------

@app.route("/s/<token>")
def helper_page(token):
    settings = get_settings()
    if token != settings["token"]:
        return render_template("404.html"), 404

    # Allow query parameter to identify device role (?role=doctor or ?as=doctor)
    role_param = request.args.get("role") or request.args.get("as")
    if role_param in ("doctor", "family", "patient"):
        session["role"] = role_param

    current_role = session.get("role")

    # If the user on this device is a Doctor, open the Doctor Confirm view
    if current_role == "doctor":
        return render_template(
            "doctor_confirm.html",
            token=token,
            patient=PATIENT,
            doctor=DOCTOR,
            reasons=DOCTOR_REASONS,
        )
    elif current_role == "family":
        return redirect(url_for("family_home"))
    elif current_role == "patient" and not request.args.get("preview"):
        return redirect(url_for("patient_home"))

    # Otherwise, render the Stranger/Bystander HELPER page
    preview = request.args.get("preview") == "1"
    event_id = None

    if not preview:
        # Dedupe within 45 seconds
        cutoff = utc_ts(utc_now() - timedelta(seconds=SCAN_DEDUPE_SECONDS))
        recent_scan = get_db().execute(
            "SELECT id FROM events WHERE kind='helper_scan' AND created_at >= ? "
            "ORDER BY id DESC LIMIT 1",
            (cutoff,),
        ).fetchone()

        if recent_scan:
            event_id = recent_scan["id"]
        else:
            event_id = log_event(
                kind="helper_scan",
                text=f"Emergency card scanned by a bystander helper.",
                place="Emergency Scan Location",
            )

    lang = request.args.get("lang", "en").lower()
    t = TRANSLATIONS_HI if lang == "hi" else TRANSLATIONS_EN

    return render_template(
        "helper.html",
        token=token,
        settings=settings,
        patient=PATIENT,
        event_id=event_id,
        preview=preview,
        lang=lang,
        t=t,
    )


@app.route("/s/<token>/location", methods=["POST"])
def helper_location(token):
    settings = get_settings()
    if token != settings["token"]:
        return jsonify(ok=False, error="Invalid token"), 404

    data = request.get_json(silent=True) or {}
    try:
        event_id = int(data.get("event_id"))
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="Invalid coordinates or event ID"), 400

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return jsonify(ok=False, error="Coordinates out of range"), 400

    # Validate event is a recent helper_scan (within 60 mins)
    cutoff = utc_ts(utc_now() - timedelta(minutes=60))
    ev = get_db().execute(
        "SELECT id FROM events WHERE id=? AND kind='helper_scan' AND created_at >= ?",
        (event_id, cutoff),
    ).fetchone()

    if not ev:
        return jsonify(ok=False, error="Expired or invalid scan event"), 404

    get_db().execute(
        "UPDATE events SET lat=?, lng=?, text=?, place=? WHERE id=?",
        (
            lat,
            lng,
            f"Helper shared GPS location with family ({lat:.4f}, {lng:.4f}).",
            "Bystander GPS Location",
            event_id,
        ),
    )
    get_db().commit()
    return jsonify(ok=True)


# -----------------------------------------------------------------------------
# Doctor Portal & Clinical Actions
# -----------------------------------------------------------------------------

@app.route("/doctor")
def doctor_home():
    session["role"] = "doctor"
    active_grant = check_active_doctor_grant()
    rows = get_db().execute(
        "SELECT * FROM events WHERE kind IN ('record_access', 'clinical_note', 'doctor_update', 'access_ended', 'hospital_scan') "
        "ORDER BY id DESC LIMIT 15"
    ).fetchall()
    recent_events = [format_event_view(r) for r in rows]

    return render_template(
        "doctor.html",
        doctor=DOCTOR,
        active_grant=active_grant,
        recent_events=recent_events,
    )


@app.route("/doctor/open/<token>", methods=["POST"])
def doctor_open(token):
    session["role"] = "doctor"
    settings = get_settings()
    if token != settings["token"]:
        return render_template("404.html"), 404

    reason = request.form.get("reason", "").strip()
    if reason not in DOCTOR_REASONS:
        flash("Please select a valid clinical justification for record access.", "danger")
        return redirect(url_for("helper_page", token=token))

    # Log record_access
    log_event(
        kind="record_access",
        reason=reason,
        text=f"{DOCTOR['name']} accessed full medical record ({reason}).",
        place=DOCTOR["hospital"],
    )

    # Log one hospital_scan per hour
    cutoff = utc_ts(utc_now() - timedelta(hours=1))
    recent_hospital = get_db().execute(
        "SELECT id FROM events WHERE kind='hospital_scan' AND created_at >= ?",
        (cutoff,),
    ).fetchone()

    if not recent_hospital:
        log_event(
            kind="hospital_scan",
            text=f"Patient arrived at {DOCTOR['hospital']}, {DOCTOR['hospital_address']}.",
            lat=DOCTOR["lat"],
            lng=DOCTOR["lng"],
            place=DOCTOR["hospital"],
        )

    flash("30-minute emergency access grant active.", "success")
    return redirect(url_for("doctor_record"))


@app.route("/doctor/record")
def doctor_record():
    session["role"] = "doctor"
    grant = check_active_doctor_grant()
    if not grant:
        flash("No active emergency access grant. Please scan the patient's card to obtain access.", "danger")
        return redirect(url_for("doctor_home"))

    # Calculate age
    dob = datetime.strptime(PATIENT["dob"], "%Y-%m-%d").date()
    today = datetime.now(IST).date()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    return render_template(
        "doctor_record.html",
        patient=PATIENT,
        doctor=DOCTOR,
        age=age,
        remaining_seconds=grant["seconds_left"],
        presets=DOCTOR_PRESET_UPDATES,
    )


@app.route("/doctor/note", methods=["POST"])
def doctor_note():
    session["role"] = "doctor"
    grant = check_active_doctor_grant()
    if not grant:
        flash("Access session expired. Please re-authenticate.", "danger")
        return redirect(url_for("doctor_home"))

    note = request.form.get("note", "").strip()
    if note:
        log_event(
            kind="clinical_note",
            text=f"{DOCTOR['name']} added clinical note: {note}",
            place=DOCTOR["hospital"],
        )
        flash("Clinical note appended to emergency audit log.", "success")

    return redirect(url_for("doctor_record"))


@app.route("/doctor/update", methods=["POST"])
def doctor_update():
    session["role"] = "doctor"
    grant = check_active_doctor_grant()
    if not grant:
        flash("Access session expired. Please re-authenticate.", "danger")
        return redirect(url_for("doctor_home"))

    update_text = request.form.get("update_text", "").strip()
    if update_text:
        log_event(
            kind="doctor_update",
            text=f"Doctor Update ({DOCTOR['hospital']}): {update_text}",
            place=DOCTOR["hospital"],
        )
        flash("Status update broadcasted to family dashboard.", "success")

    return redirect(url_for("doctor_record"))


@app.route("/doctor/end", methods=["POST"])
def doctor_end():
    session["role"] = "doctor"
    log_event(
        kind="access_ended",
        text=f"{DOCTOR['name']} concluded emergency clinical session.",
        place=DOCTOR["hospital"],
    )
    flash("Emergency session terminated. Medical records locked.", "info")
    return redirect(url_for("doctor_home"))


# -----------------------------------------------------------------------------
# Cardholder (Patient) Portal
# -----------------------------------------------------------------------------

@app.route("/patient")
def patient_home():
    session["role"] = "patient"
    settings = get_settings()
    rows = get_db().execute("SELECT * FROM events ORDER BY id DESC LIMIT 40").fetchall()
    events = [format_event_view(r) for r in rows]

    return render_template(
        "patient.html",
        patient=PATIENT,
        settings=settings,
        events=events,
    )


@app.route("/patient/reissue", methods=["POST"])
def patient_reissue():
    session["role"] = "patient"
    new_token = f"asha-{secrets.token_urlsafe(8)}"
    get_db().execute("UPDATE settings SET token=?", (new_token,))
    get_db().commit()
    log_event(
        kind="access_ended",
        text="Cardholder issued a new LifeCard. Previous emergency QR and NFC link revoked.",
    )
    flash("New LifeCard issued successfully! Your previous QR code is now permanently revoked.", "success")
    return redirect(url_for("patient_home"))


@app.route("/api/consent", methods=["POST"])
def api_consent():
    data = request.get_json(silent=True) or {}
    allowed = ("share_phone", "share_address", "share_blood", "share_alerts")

    updates = []
    vals = []
    for k in allowed:
        if k in data:
            updates.append(f"{k} = ?")
            vals.append(1 if data[k] else 0)

    if updates:
        sql = f"UPDATE settings SET {', '.join(updates)}"
        get_db().execute(sql, vals)
        get_db().commit()

    return jsonify(ok=True, settings=dict(get_settings()))


# -----------------------------------------------------------------------------
# Family Dashboard
# -----------------------------------------------------------------------------

def compute_family_state():
    """Computes status banner, 4-step journey progress, and map coordinates."""
    rows = get_db().execute("SELECT * FROM events ORDER BY id DESC LIMIT 30").fetchall()
    events = [format_event_view(r) for r in rows]

    kinds = [e["kind"] for e in events]
    has_scan = "helper_scan" in kinds
    has_location = any(e.get("lat") and e.get("lng") and e["kind"] == "helper_scan" for e in events)
    has_hospital = "hospital_scan" in kinds
    has_doctor_update = "doctor_update" in kinds or "clinical_note" in kinds

    # Journey step: 0 to 4
    current_step = 0
    if has_scan:
        current_step = 1
    if has_location:
        current_step = 2
    if has_hospital:
        current_step = 3
    if has_doctor_update:
        current_step = 4

    # Status banner
    if has_hospital:
        status = {
            "cls": "hospital-reached",
            "title": "Asha Reached City General Hospital",
            "subtitle": f"Emergency Dept &bull; Attending: {DOCTOR['name']} (Sector 44, Gurugram)",
            "badgeCls": "badge-navy",
            "badgeText": "AT HOSPITAL",
        }
    elif has_scan:
        status = {
            "cls": "alert-active",
            "title": "ALERT: LifeCard Scanned by Emergency Helper",
            "subtitle": "Bystander initiated assistance. Checking GPS coordinates and ambulance response.",
            "badgeCls": "badge-red",
            "badgeText": "EMERGENCY ACTIVE",
        }
    else:
        status = {
            "cls": "all-clear",
            "title": "All Clear &bull; No Active Emergency",
            "subtitle": "Asha's LifeCard is active and monitoring in standby mode.",
            "badgeCls": "badge-teal",
            "badgeText": "ALL CLEAR",
        }

    # Map Location: Latest location from events, fallback to Gurugram center
    map_loc = {"lat": 28.4595, "lng": 77.0266, "place": "Gurugram, Haryana"}
    for e in events:
        if e.get("lat") and e.get("lng"):
            map_loc = {
                "lat": e["lat"],
                "lng": e["lng"],
                "place": e.get("place") or "Emergency Location",
            }
            break

    return {
        "status": status,
        "journey": {"current": current_step},
        "map_location": map_loc,
        "events": events,
    }


@app.route("/family")
def family_home():
    session["role"] = "family"
    state = compute_family_state()
    return render_template(
        "family.html",
        status=state["status"],
        journey=state["journey"],
        map_loc=state["map_location"],
        events=state["events"],
    )


@app.route("/api/feed")
def api_feed():
    scope = request.args.get("scope", "family")
    state = compute_family_state()
    return jsonify(
        ok=True,
        scope=scope,
        status=state["status"],
        journey=state["journey"],
        map_location=state["map_location"],
        events=state["events"],
    )


# -----------------------------------------------------------------------------
# Dynamic QR & Pillow Card Generation
# -----------------------------------------------------------------------------

@app.route("/qr.png")
def qr_png():
    token = get_current_token()
    target_url = f"{public_base()}/s/{token}"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B1D3A", back_color="#FFFFFF")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


def load_font(size, bold=False):
    font_names = (
        ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    )
    font_dirs = [
        "C:/Windows/Fonts/",
        "/usr/share/fonts/truetype/dejavu/",
        "/Library/Fonts/",
    ]
    for d in font_dirs:
        for f in font_names:
            p = os.path.join(d, f)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


@app.route("/card.png")
def card_png():
    """Generates a crisp 1012x638 Pillow render of LifeCard."""
    token = get_current_token()
    target_url = f"{public_base()}/s/{token}"

    W, H = 1012, 638
    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Navy Header
    draw.rectangle([(0, 0), (W, 110)], fill="#0B1D3A")
    draw.text((40, 24), "EMERGENCY MEDICAL CARD", font=load_font(38, bold=True), fill="#FFFFFF")
    draw.text((40, 72), "CONSENT-BASED PATIENT BRIDGE &bull; PS-40", font=load_font(18), fill="#14B8A6")

    # Teal/Navy Bottom Banner
    draw.rectangle([(0, H - 76), (W, H)], fill="#0F766E")
    draw.text((40, H - 52), "Scan QR with smartphone camera  |  NFC Tap to Open", font=load_font(26, bold=True), fill="#FFFFFF")

    # Patient Illustrated Avatar
    avatar_size = 200
    avatar_path = os.path.join(STATIC_DIR, "avatars", "asha.png")
    if os.path.exists(avatar_path):
        av_img = Image.open(avatar_path).convert("RGBA")
        av_img = av_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
        img.paste(av_img, (40, 150), mask)
    else:
        draw.ellipse([(40, 150), (40 + avatar_size, 150 + avatar_size)], fill="#E2E8F0")

    # Cardholder Details
    draw.text((270, 150), PATIENT["name"], font=load_font(44, bold=True), fill="#0B1D3A")
    draw.text((270, 210), f"Blood Group: {PATIENT['blood_group']}", font=load_font(26, bold=True), fill="#D32F2F")
    draw.text((270, 250), f"Emergency: {PATIENT['emergency_name']} ({PATIENT['emergency_relation']})", font=load_font(22), fill="#334155")
    draw.text((270, 285), f"Phone: {PATIENT['emergency_phone']}", font=load_font(22), fill="#0F766E")
    draw.text((270, 325), f"Card Token: {token[:8].upper()}", font=load_font(20, bold=True), fill="#64748B")

    # QR Code Box
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=1)
    qr.add_data(target_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0B1D3A", back_color="#FFFFFF").convert("RGB")
    qr_img = qr_img.resize((270, 270), Image.Resampling.LANCZOS)

    draw.rectangle([(690, 140), (972, 422)], outline="#0B1D3A", width=4)
    img.paste(qr_img, (696, 146))
    draw.text((720, 432), "Scan for Emergency Info", font=load_font(18, bold=True), fill="#0B1D3A")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    download = request.args.get("download") == "1"
    return send_file(
        buf,
        mimetype="image/png",
        as_attachment=download,
        download_name="LifeCard_Asha_Sharma.png" if download else None,
    )


# -----------------------------------------------------------------------------
# Presenter Console (/demo)
# -----------------------------------------------------------------------------

@app.route("/demo")
def presenter_demo():
    token = get_current_token()
    cur = get_db().cursor()
    cur.execute("SELECT COUNT(*) FROM events")
    events_count = cur.fetchone()[0]
    active_grant = check_active_doctor_grant()

    return render_template(
        "demo.html",
        current_token=token,
        events_count=events_count,
        active_grant=active_grant,
    )


@app.route("/demo/<action>", methods=["POST"])
def demo_action(action):
    token = get_current_token()

    if action == "scan":
        log_event(
            kind="helper_scan",
            text="Simulated helper scan triggered from Presenter Console.",
            place="Gurugram Public Street",
        )
        flash("Simulated helper scan logged! Family alert dispatched.", "success")

    elif action == "location":
        loc = random.choice(DEMO_LOCATIONS)
        log_event(
            kind="helper_scan",
            text=f"Simulated GPS location dispatched ({loc['lat']:.4f}, {loc['lng']:.4f}).",
            lat=loc["lat"],
            lng=loc["lng"],
            place=loc["name"],
        )
        flash(f"Simulated GPS location shared ({loc['name']})!", "success")

    elif action == "hospital":
        log_event(
            kind="hospital_scan",
            text=f"Patient arrived at {DOCTOR['hospital']}, {DOCTOR['hospital_address']}.",
            lat=DOCTOR["lat"],
            lng=DOCTOR["lng"],
            place=DOCTOR["hospital"],
        )
        flash(f"Hospital scan logged: Patient arrived at {DOCTOR['hospital']}!", "success")

    elif action == "update":
        update_text = random.choice(DOCTOR_PRESET_UPDATES)
        log_event(
            kind="doctor_update",
            text=f"Doctor Update ({DOCTOR['hospital']}): {update_text}",
            place=DOCTOR["hospital"],
        )
        flash("Simulated doctor reassurance update dispatched to family feed!", "success")

    elif action == "reset":
        get_db().execute("DELETE FROM events")
        get_db().execute(
            "UPDATE settings SET token='asha-demo-token', share_phone=1, share_address=1, share_blood=1, share_alerts=1"
        )
        get_db().commit()
        flash("Demo database reset to clean default state.", "info")

    return redirect(url_for("presenter_demo"))


# -----------------------------------------------------------------------------
# Error Handling
# -----------------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# -----------------------------------------------------------------------------
# Initialize DB at import
# -----------------------------------------------------------------------------

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
