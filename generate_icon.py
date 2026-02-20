#!/usr/bin/env python3
"""Generate SonosPlay app icons inspired by the Sonos aesthetic.

Produces:
    icon.png   – 1024x1024 master icon
    icon.icns  – macOS app icon
    icon.ico   – Windows app icon
"""

import math
import struct
import io
from PIL import Image, ImageDraw, ImageFilter


def draw_icon(size: int = 1024) -> Image.Image:
    """Draw the SonosPlay icon at the given size.

    Design: dark rounded square with an S-shaped arrangement of sound-wave
    arcs (Sonos-inspired) framing a clean play triangle in the center.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size / 2, size / 2

    # ── Background: rounded square ────────────────────────────────
    margin = int(size * 0.02)
    corner = int(size * 0.22)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner,
        fill=(20, 20, 20),
    )

    # ── S-shaped sound wave arcs ──────────────────────────────────
    # Upper set: arcs curving from top-left, centered above middle
    # Lower set: arcs curving from bottom-right, centered below middle
    # Together they form an S-shape reminiscent of Sonos branding.

    arc_configs = [
        # (radius_factor, thickness_factor, alpha, y_offset_factor, start_angle, end_angle)
        # --- upper arcs (bowl opens downward-right) ---
        (0.46, 0.012, 55,  -0.16, 200, 330),
        (0.38, 0.012, 70,  -0.16, 200, 330),
        (0.30, 0.012, 90,  -0.16, 200, 330),
        # --- lower arcs (bowl opens upward-left) ---
        (0.46, 0.012, 55,   0.16, 20, 150),
        (0.38, 0.012, 70,   0.16, 20, 150),
        (0.30, 0.012, 90,   0.16, 20, 150),
    ]

    for r_fac, w_fac, alpha, y_off_fac, start, end in arc_configs:
        r = size * r_fac
        w = max(3, int(size * w_fac))
        oy = size * y_off_fac
        bbox = [cx - r, cy + oy - r, cx + r, cy + oy + r]
        draw.arc(bbox, start=start, end=end,
                 fill=(255, 255, 255, alpha), width=w)

    # ── Central play triangle ─────────────────────────────────────
    # Draw on a separate layer so arcs don't bleed into it.
    tri_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tri_draw = ImageDraw.Draw(tri_layer)

    # Play triangle pointing right, optically centered
    tri_h = size * 0.30   # height of triangle
    tri_w = tri_h * 0.9   # width (base-to-tip)
    tri_cx = cx + size * 0.025  # nudge right for optical balance
    tri_cy = cy

    points = [
        (tri_cx + tri_w * 0.5,  tri_cy),                  # right tip
        (tri_cx - tri_w * 0.5,  tri_cy - tri_h * 0.5),    # top-left
        (tri_cx - tri_w * 0.5,  tri_cy + tri_h * 0.5),    # bottom-left
    ]
    tri_draw.polygon(points, fill=(255, 255, 255))
    img = Image.alpha_composite(img, tri_layer)

    return img


def make_icns(png_image: Image.Image, path: str):
    """Create a macOS .icns file from a PIL Image."""
    sizes = [
        ("ic07", 128),
        ("ic08", 256),
        ("ic09", 512),
        ("ic10", 1024),
    ]
    entries = []
    for ostype, sz in sizes:
        resized = png_image.resize((sz, sz), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG")
        png_data = buf.getvalue()
        entry_size = 8 + len(png_data)
        entries.append(struct.pack(">4sI", ostype.encode(), entry_size) + png_data)

    body = b"".join(entries)
    total_size = 8 + len(body)
    header = struct.pack(">4sI", b"icns", total_size)
    with open(path, "wb") as f:
        f.write(header + body)


def make_ico(png_image: Image.Image, path: str):
    """Create a Windows .ico file from a PIL Image."""
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    imgs = [png_image.resize(s, Image.LANCZOS) for s in sizes]
    imgs[0].save(path, format="ICO", sizes=sizes)


def main():
    print("Generating SonosPlay icon…")
    icon = draw_icon(1024)

    icon.save("icon.png")
    print("  icon.png  (1024x1024)")

    make_icns(icon, "icon.icns")
    print("  icon.icns (macOS)")

    make_ico(icon, "icon.ico")
    print("  icon.ico  (Windows)")

    print("Done!")


if __name__ == "__main__":
    main()
