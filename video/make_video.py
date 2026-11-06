"""Render a 1080x1920 vertical promo video from the two product images."""
import subprocess, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
NAVY = (27, 33, 77)
ORANGE = (226, 88, 34)
TAN = (196, 164, 132)
CREAM = (250, 246, 241)

LANG = sys.argv[1] if len(sys.argv) > 1 else "en"
T = {
    "en": dict(
        hook1="Want brighter,", hook2="glowing skin?",
        intro="Meet",
        b=["Lightens skin complexion", "Reduces pigmentation", "Preserves youthful skin"],
        ingr="L-Glutathione + Astaxanthin\nwith NAC, ALA, Vitamin C & Zinc",
        badges="Halal  •  Vegan  •  Made in Canada",
        packs="Available in 30 & 2x30 capsules",
        cta1="Tap the link", cta2="to shop now!",
    ),
    "ms": dict(
        hook1="Nak kulit nampak", hook2="cerah & berseri?",
        intro="Kenali",
        b=["Mencerahkan kulit", "Mengurangkan pigmentasi", "Kekalkan kulit awet muda"],
        ingr="L-Glutathione + Astaxanthin\ndengan NAC, ALA, Vitamin C & Zink",
        badges="Halal  •  Vegan  •  Buatan Kanada",
        packs="Ada pek 30 & 2x30 kapsul",
        cta1="Tekan link", cta2="untuk beli sekarang!",
    ),
}[LANG]

def font(p, s): return ImageFont.truetype(p, s)

bottle_src = Image.open("bottle.jpg").convert("RGB")
box_src = Image.open("box.jpg").convert("RGB")
bottle = bottle_src.crop((20, 140, 390, 900))     # bottle + MAL no.
box = box_src.crop((15, 390, 440, 895))           # box + MAL no.
badges = bottle_src.crop((505, 750, 880, 895))
logo = bottle_src.crop((100, 50, 460, 130))

def ease(t):  # easeOutCubic, clamped
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def bg():
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    return im

BG = bg()

def paste_scaled(canvas, img, cx, cy, h, alpha=1.0):
    s = h / img.height
    im = img.resize((max(1, int(img.width * s)), max(1, int(h))), Image.LANCZOS)
    mask = Image.new("L", im.size, int(255 * max(0, min(1, alpha))))
    canvas.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), mask)

def text(canvas, s, cx, y, size, color, alpha=1.0, f=BOLD, shift=0):
    if alpha <= 0: return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fnt = font(f, size)
    for i, line in enumerate(s.split("\n")):
        w = d.textlength(line, font=fnt)
        d.text((cx - w / 2, y + shift + i * size * 1.25), line, font=fnt,
               fill=color + (int(255 * min(1, alpha)),))
    canvas.alpha_composite(layer)

def pill(canvas, s, cx, y, size, alpha, shift=0):
    if alpha <= 0: return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fnt = font(BOLD, size)
    w = d.textlength(s, font=fnt)
    a = int(255 * min(1, alpha))
    x0, y0 = cx - w / 2 - 50, y + shift
    d.rounded_rectangle((x0, y0, cx + w / 2 + 50, y0 + size + 50), radius=(size + 50) // 2,
                        fill=NAVY + (a,))
    d.ellipse((x0 + 22, y0 + (size + 50) / 2 - 9, x0 + 40, y0 + (size + 50) / 2 + 9), fill=TAN + (a,))
    d.text((cx - w / 2 + 10, y0 + 25), s, font=fnt, fill=(255, 255, 255, a))
    canvas.alpha_composite(layer)

# Scene timing (seconds)
DUR = 17.0

def frame(t):
    c = BG.copy().convert("RGBA")
    paste_scaled(c, logo, W / 2, 120, 90)

    if t < 3.2:  # HOOK
        a = ease(t / 0.6) * (1 - ease((t - 2.8) / 0.4))
        text(c, T["hook1"], W / 2, 620, 100, NAVY, a, shift=(1 - ease(t / 0.6)) * 60)
        a2 = ease((t - 0.5) / 0.6) * (1 - ease((t - 2.8) / 0.4))
        text(c, T["hook2"], W / 2, 750, 100, ORANGE, a2, shift=(1 - ease((t - 0.5) / 0.6)) * 60)
        # bottle peeking up from bottom
        p = ease((t - 1.0) / 1.2) * (1 - ease((t - 2.8) / 0.4))
        paste_scaled(c, bottle, W / 2, H + 300 - p * 500, 900, p)
    elif t < 6.5:  # PRODUCT REVEAL
        lt = t - 3.2
        a = ease(lt / 0.5) * (1 - ease((lt - 3.0) / 0.3))
        text(c, T["intro"], W / 2, 300, 64, NAVY, a, f=REG)
        text(c, "Asta-Glutathione +", W / 2, 390, 92, NAVY, a)
        zoom = 1000 + 120 * ease(lt / 3.3)
        paste_scaled(c, bottle, W / 2, 1180, zoom, a)
    elif t < 11.5:  # BENEFITS
        lt = t - 6.5
        out = 1 - ease((lt - 4.7) / 0.3)
        paste_scaled(c, bottle, W / 2, 1380, 820, ease(lt / 0.4) * out)
        for i, b in enumerate(T["b"]):
            st = 0.2 + i * 0.9
            a = ease((lt - st) / 0.5) * out
            pill(c, b, W / 2, 330 + i * 170, 54, a, shift=(1 - ease((lt - st) / 0.5)) * 50)
    elif t < 14.0:  # INGREDIENTS + BADGES
        lt = t - 11.5
        a = ease(lt / 0.5) * (1 - ease((lt - 2.2) / 0.3))
        text(c, T["ingr"], W / 2, 330, 58, NAVY, a)
        paste_scaled(c, badges, W / 2, 760, 300, a)
        text(c, T["badges"], W / 2, 960, 48, ORANGE, a)
        paste_scaled(c, bottle, W / 2, 1420, 640, a)
    else:  # PACKS + CTA
        lt = t - 14.0
        a = ease(lt / 0.5)
        text(c, T["packs"], W / 2, 280, 60, NAVY, a)
        paste_scaled(c, bottle, W / 2 - 250, 830, 700, a)
        paste_scaled(c, box, W / 2 + 200, 860, 520, ease((lt - 0.3) / 0.5))
        ca = ease((lt - 0.8) / 0.5)
        pulse = 1 + 0.04 * math.sin(lt * 6) * ca
        layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bw, bh = 820 * pulse, 300 * pulse
        d.rounded_rectangle((W / 2 - bw / 2, 1380 - bh / 2, W / 2 + bw / 2, 1380 + bh / 2),
                            radius=60, fill=ORANGE + (int(255 * ca),))
        c.alpha_composite(layer)
        text(c, T["cta1"], W / 2, 1290, 84, (255, 255, 255), ca)
        text(c, T["cta2"], W / 2, 1390, 70, (255, 255, 255), ca)
        text(c, "v  v  v", W / 2, 1600 + 15 * math.sin(lt * 5), 60, NAVY, ca)
    d = ImageDraw.Draw(c)
    d.rectangle((0, H - 120, W, H - 110), fill=ORANGE)
    d.rectangle((0, H - 110, W, H), fill=TAN)
    return c.convert("RGB")

out = f"asta_glutathione_promo_{LANG}.mp4"
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                       "-movflags", "+faststart", out], stdin=subprocess.PIPE)
for n in range(int(DUR * FPS)):
    ff.stdin.write(frame(n / FPS).tobytes())
ff.stdin.close(); ff.wait()
print("wrote", out)
