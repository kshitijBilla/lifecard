"""Tiny SQLite layer built on the standard library only.

Two tables: one settings row (token + four consent switches) and an append-only
events log. Every timestamp is stored as naive UTC ISO text; formatting into IST
happens in the Jinja filters.
"""

import contextlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from data import GRANT_MINUTES

if os.environ.get("VERCEL"):
    DB_PATH = os.environ.get("DB_PATH", "/tmp/lifecard.db")
else:
    DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "lifecard.db"))
DEFAULT_TOKEN = "asha-demo-token"

EVENT_KINDS = (
    "helper_scan",
    "hospital_scan",
    "doctor_update",
    "record_access",
    "access_ended",
    "clinical_note",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    id             INTEGER PRIMARY KEY CHECK (id = 1),
    token          TEXT    NOT NULL,
    share_phone    INTEGER NOT NULL DEFAULT 1,
    share_address  INTEGER NOT NULL DEFAULT 1,
    share_blood    INTEGER NOT NULL DEFAULT 1,
    share_alerts   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT NOT NULL,
    reason     TEXT,
    text       TEXT,
    lat        REAL,
    lng        REAL,
    place      TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_created ON events (created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events (kind, id DESC);
"""

CONSENT_KEYS = ("share_phone", "share_address", "share_blood", "share_alerts")


def utcnow():
    """Naive UTC now - everything in the DB is stored in this shape."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse(value):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return utcnow()


def db_path():
    return os.environ.get("DB_PATH", DB_PATH)


@contextlib.contextmanager
def connect():
    """A connection that commits on success and always closes.

    sqlite3's own `with conn:` only manages the transaction, never the handle,
    so the connection has to be closed here or every request leaks one.
    """
    conn = sqlite3.connect(db_path(), timeout=10, check_same_thread=False)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        with conn:
            yield conn
    finally:
        conn.close()


def init_db(seed=True):
    """Create the schema and make sure the single settings row exists."""
    folder = os.path.dirname(db_path())
    if folder:
        os.makedirs(folder, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
        if seed:
            conn.execute(
                "INSERT OR IGNORE INTO settings (id, token, share_phone, share_address,"
                " share_blood, share_alerts) VALUES (1, ?, 1, 1, 1, 1)",
                (DEFAULT_TOKEN,),
            )


def get_settings():
    with connect() as conn:
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    if row is None:
        init_db()
        with connect() as conn:
            row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    return {
        "token": row["token"],
        "share_phone": bool(row["share_phone"]),
        "share_address": bool(row["share_address"]),
        "share_blood": bool(row["share_blood"]),
        "share_alerts": bool(row["share_alerts"]),
    }


def token():
    return get_settings()["token"]


def set_consent(key, value):
    if key not in CONSENT_KEYS:
        raise ValueError("unknown consent key: %r" % (key,))
    with connect() as conn:
        conn.execute("UPDATE settings SET %s = ? WHERE id = 1" % key, (1 if value else 0,))
    return get_settings()


def rotate_token():
    """Issue a brand new card token. The old QR stops resolving immediately."""
    new = "asha-" + secrets.token_urlsafe(9).replace("_", "-").replace("-", "")[:10].lower()
    with connect() as conn:
        conn.execute("UPDATE settings SET token = ? WHERE id = 1", (new,))
    return new


def add_event(kind, reason=None, text=None, lat=None, lng=None, place=None, created_at=None):
    if kind not in EVENT_KINDS:
        raise ValueError("unknown event kind: %r" % (kind,))
    stamp = iso(created_at or utcnow())
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO events (kind, reason, text, lat, lng, place, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (kind, reason, text, lat, lng, place, stamp),
        )
        return cur.lastrowid


def update_event_location(event_id, lat, lng, place=None):
    with connect() as conn:
        cur = conn.execute(
            "UPDATE events SET lat = ?, lng = ?, place = COALESCE(?, place) WHERE id = ?",
            (lat, lng, place, event_id),
        )
        return cur.rowcount > 0


def get_event(event_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return dict(row) if row else None


def events(limit=80, kinds=None):
    """Newest first. Ties on created_at break by id so ordering is stable."""
    sql = "SELECT * FROM events"
    args = []
    if kinds:
        sql += " WHERE kind IN (%s)" % ",".join("?" * len(kinds))
        args.extend(kinds)
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    args.append(limit)
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def last_event(kind):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM events WHERE kind = ? ORDER BY created_at DESC, id DESC LIMIT 1",
            (kind,),
        ).fetchone()
    return dict(row) if row else None


def recent_event(kind, within_seconds):
    """Most recent event of `kind` inside the window, used for scan dedupe."""
    cutoff = iso(utcnow() - timedelta(seconds=within_seconds))
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM events WHERE kind = ? AND created_at >= ?"
            " ORDER BY created_at DESC, id DESC LIMIT 1",
            (kind, cutoff),
        ).fetchone()
    return dict(row) if row else None


def active_grant():
    """The live record_access grant, or None.

    A grant lasts GRANT_MINUTES and is killed early by any access_ended logged
    after it.
    """
    grant = last_event("record_access")
    if not grant:
        return None
    started = parse(grant["created_at"])
    expires = started + timedelta(minutes=GRANT_MINUTES)
    if expires <= utcnow():
        return None
    ended = last_event("access_ended")
    if ended and parse(ended["created_at"]) >= started:
        return None
    grant["expires_at"] = expires
    grant["seconds_left"] = max(0, int((expires - utcnow()).total_seconds()))
    return grant


def end_access():
    if active_grant():
        return add_event("access_ended", text="Doctor ended the record session")
    return None


def reset(seed_token=DEFAULT_TOKEN):
    """Presenter console reset: clean slate, default token, all consent on."""
    with connect() as conn:
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'events'")
        conn.execute(
            "UPDATE settings SET token = ?, share_phone = 1, share_address = 1,"
            " share_blood = 1, share_alerts = 1 WHERE id = 1",
            (seed_token,),
        )
