"""Pillow renderers: the QR code and the downloadable 1012x638 wallet card."""

import io
import os

import qrcode
from qrcode.constants import ERROR_CORRECT_Q
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE, "static", "fonts")
AVATAR_DIR = os.path.join(BASE, "static", "avatars")

CARD_W, CARD_H = 1012, 638

NAVY = (11, 29, 58)
NAVY_MID = (22, 48, 94)
NAVY_SOFT = (30, 64, 120)
TEAL = (20, 184, 166)
RED = (211, 47, 47)
WHITE = (255, 255, 255)
MIST = (209, 221, 238)

_font_cache = {}


def font(weight="Regular", size=24):
    key = (weight, size)
    if key not in _font_cache:
        path = os.path.join(FONT_DIR, "Inter-%s.otf" % weight)
        try:
            _font_cache[key] = ImageFont.truetype(path, size)
        except OSError:
            # Bundled font missing (shouldn't happen) - stay renderable.
            _font_cache[key] = ImageFont.load_default(size=size)
    return _font_cache[key]


def qr_image(payload, box_size=10, border=2, fg=NAVY, bg=WHITE):
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_Q, box_size=box_size, border=border)
    qr.add_data(payload)
    qr.make(fit=True)
    return qr.make_image(fill_color=fg, back_color=bg).convert("RGB")


def qr_png_bytes(payload, box_size=10):
    buf = io.BytesIO()
    qr_image(payload, box_size=box_size).save(buf, "PNG", optimize=True)
    buf.seek(0)
    return buf


def _diagonal_gradient(size, top, bottom):
    w, h = size
    grad = Image.new("RGB", (1, h), top)
    px = grad.load()
    for y in range(h):
        k = y / max(1, h - 1)
        px[0, y] = (
            round(top[0] + (bottom[0] - top[0]) * k),
            round(top[1] + (bottom[1] - top[1]) * k),
            round(top[2] + (bottom[2] - top[2]) * k),
        )
    return grad.resize((w, h), Image.BILINEAR)


def _circle(img, size):
    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    img.putalpha(mask)
    return img


def _text(draw, xy, text, weight, size, fill, spacing=0):
    """Draw text, optionally letterspaced (Pillow has no tracking option)."""
    f = font(weight, size)
    if not spacing:
        draw.text(xy, text, font=f, fill=fill)
        return
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + spacing


def _chip(draw, x, y, label, bg, fg, size=22, pad_x=18, height=44):
    f = font("SemiBold", size)
    w = draw.textlength(label, font=f) + pad_x * 2
    draw.rounded_rectangle((x, y, x + w, y + height), radius=height // 2, fill=bg)
    draw.text((x + pad_x, y + (height - size) / 2 - 2), label, font=f, fill=fg)
    return w


def render_card(patient, payload, blood=True, alerts=True):
    """The downloadable card. `blood`/`alerts` follow the cardholder's consent."""
    card = Image.new("RGB", (CARD_W, CARD_H), NAVY)
    card.paste(_diagonal_gradient((CARD_W, CARD_H), NAVY_MID, NAVY), (0, 0))

    # Soft teal glow in the top-right corner.
    glow = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i, alpha in enumerate((14, 18, 22)):
        r = 420 - i * 90
        gd.ellipse((CARD_W - r + 120, -r + 40, CARD_W + r - 120, r - 40), fill=TEAL + (alpha,))
    card = Image.alpha_composite(card.convert("RGBA"), glow).convert("RGB")

    d = ImageDraw.Draw(card)

    # --- header ---------------------------------------------------------
    d.rounded_rectangle((56, 44, 100, 88), radius=14, fill=TEAL)
    d.text((68, 50), "+", font=font("Bold", 36), fill=NAVY)
    d.text((114, 48), "LifeCard", font=font("Bold", 34), fill=WHITE)
    _text(d, (114, 90), "CONSENT-BASED EMERGENCY RECORD", "SemiBold", 15, (138, 162, 196), spacing=1.6)
    _text(d, (CARD_W - 322, 54), "EMERGENCY MEDICAL CARD", "SemiBold", 15, (138, 162, 196), spacing=1.4)

    d.line((56, 126, CARD_W - 56, 126), fill=(40, 66, 110), width=2)

    # --- identity -------------------------------------------------------
    avatar_path = os.path.join(AVATAR_DIR, patient.get("avatar", "asha.png"))
    try:
        av = _circle(Image.open(avatar_path), 168)
        ring = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((0, 0, 179, 179), fill=TEAL + (80,))
        card.paste(ring, (50, 176), ring)
        card.paste(av, (56, 182), av)
    except OSError:
        d.ellipse((56, 182, 224, 350), fill=NAVY_SOFT)

    tx = 256
    d.text((tx, 186), patient["name"], font=font("Bold", 50), fill=WHITE)
    meta = "%s  ·  DOB %s" % (patient["sex_long"], patient["dob"])
    d.text((tx, 250), meta, font=font("Regular", 24), fill=MIST)

    y = 296
    if blood:
        w = _chip(d, tx, y, "Blood  %s" % patient["blood"], RED, WHITE, size=24, height=48)
        tx_after = tx + w + 14
    else:
        tx_after = tx
    _chip(d, tx_after, y, "Organ donor" if patient.get("organ_donor") else "ICE card", (255, 255, 255), NAVY, size=22, height=48)

    # --- alert chips ----------------------------------------------------
    y = 374
    if alerts and patient.get("alert_chips"):
        _text(d, (56, y), "MEDICAL ALERTS", "SemiBold", 15, (138, 162, 196), spacing=1.4)
        cx, cy = 56, y + 30
        for chip in patient["alert_chips"]:
            w = _chip(d, cx, cy, chip, (47, 28, 38), (255, 158, 158), size=21, height=42)
            cx += w + 12
    else:
        _text(d, (56, y), "MEDICAL ALERTS", "SemiBold", 15, (138, 162, 196), spacing=1.4)
        d.text((56, y + 32), "Hidden by the cardholder", font=font("Regular", 21), fill=(120, 142, 176))

    # --- emergency contact ---------------------------------------------
    ec = patient["emergency_contact"]
    _text(d, (56, 470), "EMERGENCY CONTACT", "SemiBold", 15, (138, 162, 196), spacing=1.4)
    d.text((56, 500), "%s (%s)" % (ec["name"], ec["relation"]), font=font("SemiBold", 24), fill=WHITE)
    d.text((56, 534), ec["phone"], font=font("Regular", 24), fill=MIST)

    # --- QR panel -------------------------------------------------------
    panel_x, panel_y, panel_s = CARD_W - 56 - 268, 182, 268
    d.rounded_rectangle((panel_x, panel_y, panel_x + panel_s, panel_y + panel_s + 56), radius=28, fill=WHITE)
    qr = qr_image(payload, box_size=10, border=1).resize((panel_s - 48, panel_s - 48), Image.NEAREST)
    card.paste(qr, (panel_x + 24, panel_y + 24))
    cap = "Scan or tap in an emergency"
    cap_f = font("SemiBold", 18)
    cap_w = d.textlength(cap, font=cap_f)
    d.text((panel_x + (panel_s - cap_w) / 2, panel_y + panel_s + 12), cap, font=cap_f, fill=NAVY)

    # NFC waves beside the panel caption.
    nx, ny = panel_x - 18, panel_y + panel_s + 70
    for i, r in enumerate((10, 20, 30)):
        d.arc((nx - r, ny - r, nx + r, ny + r), start=-55, end=55, fill=(138, 162, 196), width=4)
    d.text((nx + 42, ny - 14), "NFC enabled", font=font("Regular", 20), fill=(138, 162, 196))

    # --- footer ---------------------------------------------------------
    d.text((56, 584), "Demo card · fictional data · every access is logged for the cardholder",
           font=font("Regular", 19), fill=(108, 132, 170))

    return card


def card_png_bytes(patient, payload, blood=True, alerts=True):
    buf = io.BytesIO()
    render_card(patient, payload, blood=blood, alerts=alerts).save(buf, "PNG", optimize=True)
    buf.seek(0)
    return buf
