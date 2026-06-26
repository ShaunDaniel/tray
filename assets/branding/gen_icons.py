"""Regenerate all RisePrint visual assets from the Rise master art.

  python assets/branding/gen_icons.py

Masters (in this dir): rise-icon.png (1024 square app tile), rise-wordmark.png
(the 'rise' wordmark). Pillow only -- no ImageMagick/rsvg needed. Covers every
Windows-facing surface; macOS/Linux SVGs are also swapped (see RISE_FORK.md).
"""
import glob, os
from PIL import Image, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
RES = os.path.join(REPO, "src", "qz", "ui", "resources")
NSIS = os.path.join(REPO, "ant", "windows", "nsis")

TILE = Image.open(os.path.join(HERE, "rise-icon.png")).convert("RGBA")     # coral tile + white triangle
WORD = Image.open(os.path.join(HERE, "rise-wordmark.png")).convert("RGBA")  # 'rise' wordmark
DARK = (63, 42, 43, 255)  # #3F2A2B for the mono tray mask

# Triangle geometry (rise-icon.svg, 1024 viewBox) for the monochrome mask icons
TRI = [(622.9, 691.2), (286.4, 693.8), (622.9, 264.4)]
txs = [p[0] for p in TRI]; tys = [p[1] for p in TRI]
tminx, tminy = min(txs), min(tys); tw, th = max(txs) - tminx, max(tys) - tminy
SS = 4


def fit(src, w, h, pad=0.0):
    """Contain src in a transparent w*h canvas, centered."""
    iw, ih = src.size
    scale = min(w * (1 - 2 * pad) / iw, h * (1 - 2 * pad) / ih)
    r = src.resize((max(1, round(iw * scale)), max(1, round(ih * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(r, ((w - r.width) // 2, (h - r.height) // 2))
    return canvas


def square(size):
    return TILE.resize((size, size), Image.LANCZOS)


def mask_tri(w, h, fill=DARK, pad=0.08):
    cw, ch = w * SS, h * SS
    scale = min(cw * (1 - 2 * pad) / tw, ch * (1 - 2 * pad) / th)
    ox, oy = (cw - tw * scale) / 2, (ch - th * scale) / 2
    img = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    pts = [(ox + (x - tminx) * scale, oy + (y - tminy) * scale) for x, y in TRI]
    ImageDraw.Draw(img).polygon(pts, fill=fill)
    return img.resize((w, h), Image.LANCZOS)


def _font(name, size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()


def _centered(d, y, text, font, w=164, fill=(255, 255, 255, 255)):
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2, y), text, fill=fill, font=font)


def installer_bmps():
    """Rise-branded NSIS wizard graphics (24-bit BMP, MUI standard sizes)."""
    # Welcome/finish side banner, 164x314: coral panel, white mark + name
    w = Image.new("RGBA", (164, 314), (255, 127, 104, 255))
    w.alpha_composite(mask_tri(96, 96, fill=(255, 255, 255, 255)), (34, 48))
    d = ImageDraw.Draw(w)
    _centered(d, 170, "RisePrint", _font("arialbd.ttf", 26))
    _centered(d, 290, "Rising Dine Pvt. Ltd.", _font("arial.ttf", 12))
    w.convert("RGB").save(os.path.join(NSIS, "welcome.bmp"), "BMP")
    print("ant/windows/nsis/welcome.bmp 164x314")
    # Header strip, 150x57: Rise tile at right on white (top-right of inner pages)
    h = Image.new("RGBA", (150, 57), (255, 255, 255, 255))
    icon = TILE.resize((45, 45), Image.LANCZOS)
    h.alpha_composite(icon, (99, 6))
    h.convert("RGB").save(os.path.join(NSIS, "header.bmp"), "BMP")
    print("ant/windows/nsis/header.bmp 150x57")


def save_ico(path, img):
    sizes = [(s, s) for s in (16, 24, 32, 48, 64, 96, 128, 256)]
    img.resize((256, 256), Image.LANCZOS).save(path, format="ICO", sizes=sizes)


def redraw(path, img):
    w, h = Image.open(path).size
    (img if img.size == (w, h) else fit(img, w, h)).save(path)
    print(f"{os.path.relpath(path, REPO)} {w}x{h}")


if __name__ == "__main__":
    # Color tray icons -> the app tile
    for p in glob.glob(os.path.join(RES, "qz-default*.png")):
        w, h = Image.open(p).size
        square(w).save(p); print(f"{os.path.relpath(p, REPO)} {w}x{h}")
    # Mono mask tray icons -> dark triangle silhouette
    for p in glob.glob(os.path.join(RES, "qz-mask*.png")):
        w, h = Image.open(p).size
        mask_tri(w, h).save(p); print(f"{os.path.relpath(p, REPO)} {w}x{h}")
    # About logo (square) -> tile; banner (wide) -> wordmark
    redraw(os.path.join(RES, "qz-logo.png"), TILE)
    redraw(os.path.join(RES, "qz-banner.png"), fit(WORD, *Image.open(os.path.join(RES, "qz-banner.png")).size, pad=0.12))

    # Windows .ico set
    save_ico(os.path.join(HERE, "windows-icon.ico"), TILE); print("assets/branding/windows-icon.ico")
    save_ico(os.path.join(NSIS, "console.ico"), TILE); print("ant/windows/nsis/console.ico")
    save_ico(os.path.join(NSIS, "uninstall.ico"), ImageOps.grayscale(TILE).convert("RGBA")); print("ant/windows/nsis/uninstall.ico (grayscale)")

    # NSIS installer wizard graphics
    installer_bmps()

    # macOS/Linux vector identity + best-effort .icns
    svg = open(os.path.join(HERE, "rise-icon.svg"), encoding="utf-8").read()
    for name in ("apple-icon.svg", "linux-icon.svg"):
        open(os.path.join(HERE, name), "w", encoding="utf-8").write(svg); print(f"assets/branding/{name}")
    try:
        TILE.save(os.path.join(HERE, "apple-icon.icns")); print("assets/branding/apple-icon.icns")
    except Exception as e:
        print(f"apple-icon.icns skipped ({e})")
