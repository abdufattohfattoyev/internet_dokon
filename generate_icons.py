"""
OptimHalolMarket PWA ikonkalarini generatsiya qilish.
Agar static/logo.png mavjud bo'lsa — undan foydalanadi.
Aks holda — yashil brand ikonkasi yaratiladi.
"""
import os, math
from PIL import Image, ImageDraw

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
LOGO_PATH  = os.path.join(STATIC_DIR, "logo.png")

GREEN      = (22, 163, 74)
GREEN_D    = (15, 118, 55)
WHITE      = (255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


def make_brand_icon(size):
    """Logo yo'q bo'lganda yashil uy ikonkasi."""
    img  = Image.new("RGBA", (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # Yumaloq yashil fon
    rad = size // 5
    draw.rounded_rectangle([0, 0, size-1, size-1], radius=rad, fill=GREEN)

    # Yuqori yorug'lik effekti
    overlay = Image.new("RGBA", (size, size), TRANSPARENT)
    odraw   = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle([0, 0, size-1, size//2], radius=rad, fill=(255,255,255,28))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    s  = size * 0.56
    cx = size / 2
    cy = size / 2 + size * 0.02

    # Tom (uchburchak)
    roof_top = cy - s * 0.32
    roof_bot = cy - s * 0.00
    half_w   = s * 0.44
    draw.polygon([
        (cx,              roof_top),
        (cx + half_w + s*0.06, roof_bot),
        (cx - half_w - s*0.06, roof_bot),
    ], fill=WHITE)

    # Tana
    bx1 = cx - s * 0.30
    bx2 = cx + s * 0.30
    by1 = cy - s * 0.02
    by2 = cy + s * 0.38
    br  = max(2, int(size * 0.03))
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=br, fill=WHITE)

    # Eshik (teshik — yashil)
    dw = s * 0.20
    dh = s * 0.24
    dx1 = cx - dw/2
    dx2 = cx + dw/2
    dy1 = by2 - dh
    dr  = max(2, int(dw * 0.35))
    draw.rounded_rectangle([dx1, dy1, dx2, by2], radius=dr, fill=GREEN)

    # Derazalar
    wz  = s * 0.12
    wy  = by1 + (dy1 - by1) / 2 - wz / 2
    for wx in [cx - s*0.22, cx + s*0.10]:
        draw.rounded_rectangle(
            [wx, wy, wx+wz, wy+wz],
            radius=max(1, int(wz*0.2)), fill=GREEN
        )

    return img


def make_icon_from_logo(logo_path, size):
    """Mavjud logo faylidan ikonka yaratish."""
    logo = Image.open(logo_path).convert("RGBA")

    # Kvadrat canvas
    canvas = Image.new("RGBA", (size, size), TRANSPARENT)

    # Logo o'lchamini moslashtirish (padding bilan)
    pad    = int(size * 0.10)
    target = size - pad * 2
    logo.thumbnail((target, target), Image.LANCZOS)
    lw, lh = logo.size
    ox = (size - lw) // 2
    oy = (size - lh) // 2
    canvas.paste(logo, (ox, oy), logo)
    return canvas


def save_icon(img, path):
    final = Image.new("RGB", img.size, WHITE)
    final.paste(img, mask=img.split()[3])
    final.save(path, "PNG", optimize=True)
    print(f"  ✓ {os.path.basename(path)}")


def main():
    os.makedirs(STATIC_DIR, exist_ok=True)
    has_logo = os.path.exists(LOGO_PATH)

    if has_logo:
        print(f"Logo topildi: {LOGO_PATH}")
    else:
        print("Logo topilmadi — brand ikonkasi yaratiladi.")

    targets = {
        "android-chrome-192x192.png": 192,
        "android-chrome-512x512.png": 512,
        "apple-touch-icon.png":       180,
        "favicon-32x32.png":           32,
        "favicon-16x16.png":           16,
    }

    print("Ikonkalar yaratilmoqda...")
    for fname, sz in targets.items():
        if has_logo:
            icon = make_icon_from_logo(LOGO_PATH, sz)
        else:
            icon = make_brand_icon(sz)
        save_icon(icon, os.path.join(STATIC_DIR, fname))

    print("Barcha ikonkalar tayyor!\n")


if __name__ == "__main__":
    main()
