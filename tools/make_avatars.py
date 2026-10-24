#!/usr/bin/env python3
"""Generate the four flat illustrated avatars used across LifeCard.

These are drawn from scratch with Pillow - there are no photographs of real
people anywhere in this project. Run from the repo root:

    python tools/make_avatars.py
"""

import os
import sys

from PIL import Image, ImageDraw

SIZE = 512
SS = 4  # supersample factor, downscaled at the end for clean edges

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "avatars")

FACES = {
    "asha": {
        "bg": ((214, 245, 240), (178, 232, 224)),
        "skin": (226, 176, 136),
        "skin_shade": (206, 155, 116),
        "hair": (42, 32, 38),
        "hair_light": (62, 48, 56),
        "cloth": (20, 184, 166),
        "cloth_dark": (13, 148, 136),
        "style": "long_bun",
        "accent": (255, 214, 102),
    },
    "rohan": {
        "bg": ((214, 228, 250), (182, 203, 240)),
        "skin": (214, 160, 120),
        "skin_shade": (192, 138, 100),
        "hair": (30, 24, 26),
        "hair_light": (48, 40, 44),
        "cloth": (28, 58, 110),
        "cloth_dark": (18, 40, 80),
        "style": "short",
        "accent": (120, 170, 255),
    },
    "kavita": {
        "bg": ((250, 226, 230), (242, 203, 212)),
        "skin": (218, 166, 128),
        "skin_shade": (196, 144, 108),
        "hair": (86, 80, 86),
        "hair_light": (176, 172, 176),
        "cloth": (150, 48, 84),
        "cloth_dark": (120, 34, 66),
        "style": "grey_bun",
        "accent": (255, 190, 210),
    },
    "drrao": {
        "bg": ((222, 236, 252), (198, 220, 248)),
        "skin": (224, 174, 134),
        "skin_shade": (202, 152, 112),
        "hair": (38, 30, 34),
        "hair_light": (58, 46, 52),
        "cloth": (248, 250, 253),
        "cloth_dark": (214, 224, 238),
        "style": "doctor",
        "accent": (20, 184, 166),
    },
}


def vertical_gradient(size, top, bottom):
    """A simple top-to-bottom gradient tile."""
    grad = Image.new("RGB", (1, size), top)
    px = grad.load()
    for y in range(size):
        k = y / max(1, size - 1)
        px[0, y] = (
            round(top[0] + (bottom[0] - top[0]) * k),
            round(top[1] + (bottom[1] - top[1]) * k),
            round(top[2] + (bottom[2] - top[2]) * k),
        )
    return grad.resize((size, size), Image.NEAREST)


def draw_avatar(spec):
    w = SIZE * SS
    img = Image.new("RGBA", (w, w), (0, 0, 0, 0))

    # Rounded gradient plate behind the figure.
    plate = vertical_gradient(w, spec["bg"][0], spec["bg"][1]).convert("RGBA")
    mask = Image.new("L", (w, w), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, w - 1, w - 1), fill=255)
    img.paste(plate, (0, 0), mask)

    d = ImageDraw.Draw(img)
    cx = w // 2

    # Shoulders / torso wedge.
    torso_top = int(w * 0.70)
    d.ellipse(
        (int(w * 0.10), torso_top, int(w * 0.90), int(w * 1.32)),
        fill=spec["cloth"],
    )
    # Neckline shading gives the flat shapes a little depth.
    d.ellipse(
        (int(w * 0.30), torso_top - int(w * 0.02), int(w * 0.70), int(w * 0.95)),
        fill=spec["cloth_dark"],
    )

    # Neck.
    d.rounded_rectangle(
        (int(w * 0.43), int(w * 0.58), int(w * 0.57), int(w * 0.78)),
        radius=int(w * 0.05),
        fill=spec["skin_shade"],
    )

    style = spec["style"]
    head_box = (int(w * 0.29), int(w * 0.20), int(w * 0.71), int(w * 0.68))

    # Hair behind the head.
    if style in ("long_bun", "grey_bun", "doctor"):
        d.ellipse(
            (int(w * 0.25), int(w * 0.18), int(w * 0.75), int(w * 0.74)),
            fill=spec["hair"],
        )
        if style == "long_bun":
            # Bun on top.
            d.ellipse((int(w * 0.40), int(w * 0.10), int(w * 0.60), int(w * 0.26)), fill=spec["hair_light"])
        if style == "grey_bun":
            d.ellipse((int(w * 0.39), int(w * 0.09), int(w * 0.61), int(w * 0.26)), fill=spec["hair_light"])
        if style == "doctor":
            # Shoulder-length sweep.
            d.ellipse((int(w * 0.20), int(w * 0.36), int(w * 0.40), int(w * 0.84)), fill=spec["hair"])
            d.ellipse((int(w * 0.60), int(w * 0.36), int(w * 0.80), int(w * 0.84)), fill=spec["hair"])
    else:
        d.ellipse(
            (int(w * 0.27), int(w * 0.17), int(w * 0.73), int(w * 0.70)),
            fill=spec["hair"],
        )

    # Face.
    d.ellipse(head_box, fill=spec["skin"])

    # Fringe / hairline across the forehead.
    if style == "short":
        d.ellipse((int(w * 0.28), int(w * 0.16), int(w * 0.72), int(w * 0.42)), fill=spec["hair"])
        d.ellipse((int(w * 0.33), int(w * 0.26), int(w * 0.67), int(w * 0.46)), fill=spec["skin"])
    else:
        d.ellipse((int(w * 0.27), int(w * 0.17), int(w * 0.73), int(w * 0.40)), fill=spec["hair"])
        d.ellipse((int(w * 0.34), int(w * 0.25), int(w * 0.66), int(w * 0.44)), fill=spec["skin"])

    if style == "grey_bun":
        # A few lighter strands for age.
        d.ellipse((int(w * 0.30), int(w * 0.19), int(w * 0.46), int(w * 0.32)), fill=spec["hair_light"])

    # Eyes and smile - minimal, flat-illustration style.
    eye_y = int(w * 0.455)
    eye_r = int(w * 0.022)
    for ex in (int(w * 0.425), int(w * 0.575)):
        d.ellipse((ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r), fill=(44, 38, 44))
    d.arc(
        (int(w * 0.44), int(w * 0.48), int(w * 0.56), int(w * 0.58)),
        start=15,
        end=165,
        fill=(150, 86, 70),
        width=int(w * 0.012),
    )

    if style == "doctor":
        # White coat lapels + a teal stethoscope.
        d.polygon(
            [(cx, int(w * 0.80)), (int(w * 0.36), int(w * 1.05)), (int(w * 0.30), int(w * 0.80))],
            fill=spec["cloth_dark"],
        )
        d.polygon(
            [(cx, int(w * 0.80)), (int(w * 0.64), int(w * 1.05)), (int(w * 0.70), int(w * 0.80))],
            fill=spec["cloth_dark"],
        )
        d.arc(
            (int(w * 0.34), int(w * 0.72), int(w * 0.66), int(w * 1.00)),
            start=200,
            end=340,
            fill=spec["accent"],
            width=int(w * 0.022),
        )
        d.ellipse(
            (int(w * 0.58), int(w * 0.92), int(w * 0.68), int(w * 1.02)),
            fill=spec["accent"],
        )
    elif style == "grey_bun":
        # Saree-style drape over one shoulder.
        d.polygon(
            [(int(w * 0.30), int(w * 0.84)), (int(w * 0.52), int(w * 1.10)), (int(w * 0.22), int(w * 1.10))],
            fill=spec["cloth_dark"],
        )
    else:
        # Collar notch.
        d.polygon(
            [(cx, int(w * 0.86)), (int(w * 0.44), int(w * 0.76)), (int(w * 0.56), int(w * 0.76))],
            fill=spec["cloth_dark"],
        )

    # Clip everything back to the circular plate.
    out = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, spec in FACES.items():
        path = os.path.join(OUT_DIR, "%s.png" % name)
        draw_avatar(spec).save(path, "PNG", optimize=True)
        print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
