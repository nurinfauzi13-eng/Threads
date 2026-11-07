"""Ilustrasi baju kurung nikah guna tekstur lace sebenar dari gambar kedai.
usage: python3 baju_kurung.py lace_photo.jpg out.png
"""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 1200, 1900
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"

# ---- 1. lace texture: flatten the shop lighting, mirror-tile to fill canvas ----
photo = Image.open(SRC).convert("RGB")
patch = np.asarray(photo.crop((430, 560, 1150, 1450)), np.float32)
lum = patch.mean(2, keepdims=True)
light = np.asarray(Image.fromarray(lum[..., 0].astype(np.uint8)).filter(ImageFilter.GaussianBlur(40)),
                   np.float32)[..., None]
flat = np.clip(patch / (light + 1) * 175, 0, 255)          # even lighting
target = np.array([226, 205, 178], np.float32)              # champagne lining
flat = flat / flat.reshape(-1, 3).mean(0) * target
full = Image.fromarray(np.clip(flat, 0, 255).astype(np.uint8))
rng0 = np.random.default_rng(11)
acc = np.zeros((H, W, 3), np.float32); wsum = np.zeros((H, W, 1), np.float32)
PW, PH = 400, 480
fm = np.outer(np.hanning(PH) ** 0.5, np.hanning(PW) ** 0.5).astype(np.float32)[..., None] + 1e-3
for y in range(-200, H, 300):
    for x in range(-200, W, 260):
        for _try in range(40):  # avoid patches containing the photo's fold shadows
            sx = int(rng0.uniform(0, full.width - PW * 1.25)); sy = int(rng0.uniform(0, full.height - PH * 1.25))
            lm = np.asarray(full.crop((sx, sy, sx + int(PW * 1.25), sy + int(PH * 1.25))).convert("L").resize((50, 60)).filter(ImageFilter.GaussianBlur(2)), np.float32)
            if lm.min() > lm.mean() * 0.8: break
        pc = np.asarray(full.crop((sx, sy, sx + int(PW * 1.25), sy + int(PH * 1.25))).resize((PW, PH), Image.LANCZOS), np.float32)
        ox, oy = x + int(rng0.uniform(-40, 40)), y + int(rng0.uniform(-40, 40))
        x1, y1, x2, y2 = max(0, ox), max(0, oy), min(W, ox + PW), min(H, oy + PH)
        if x2 <= x1 or y2 <= y1: continue
        sub = (slice(y1 - oy, y2 - oy), slice(x1 - ox, x2 - ox))
        # pick the patch with more lace where weights already exist -> simple max-blend keeps motifs crisp
        acc[y1:y2, x1:x2] += pc[sub] * fm[sub] ** 3; wsum[y1:y2, x1:x2] += fm[sub] ** 3
lace = Image.fromarray(np.clip(acc / np.maximum(wsum, 1e-6), 0, 255).astype(np.uint8))

# ---- 2. background ----
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.42) / H) ** 2)
bgc = np.stack([250 - r * 40, 245 - r * 44, 238 - r * 48], -1)
canvas = Image.fromarray(np.clip(bgc, 0, 255).astype(np.uint8)).convert("RGBA")

def scallop_poly(pts_top, y_bottom, x0, x1, n, depth):
    """polygon whose bottom edge is a row of scallops (lace border)."""
    pts = list(pts_top)
    step = (x1 - x0) / n
    for i in range(n, 0, -1):
        cx = x0 + (i - 0.5) * step
        for a in np.linspace(0, math.pi, 10):
            pts.append((cx + math.cos(a) * step / 2, y_bottom + math.sin(a) * depth))
    return pts

def garment(mask_poly, shade_fn, outline=True):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(mask_poly, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    tex = np.asarray(lace, np.float32) * shade_fn()[..., None]
    layer = Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)).convert("RGBA")
    layer.putalpha(m)
    # soft drop shadow
    sh = Image.new("RGBA", (W, H), (90, 70, 50, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(18)).point(lambda v: v * 0.35))
    canvas.alpha_composite(sh, (10, 16)); canvas.alpha_composite(layer)
    if outline:
        ImageDraw.Draw(canvas).line(mask_poly + [mask_poly[0]], fill=(150, 118, 80, 110), width=2)

def folds(x_left, x_right, y_top, y_bot, n_folds, strength, flare=0.0):
    """vertical drape shading: darker at sides + soft sinusoidal folds."""
    cx = (x_left + x_right) / 2; half = (x_right - x_left) / 2
    t = np.clip((yy - y_top) / max(1, y_bot - y_top), 0, 1)
    hw = half * (1 + flare * t)
    u = np.clip((xx - cx) / hw, -1.2, 1.2)
    side = 1 - 0.16 * np.abs(u) ** 2.2
    wave = 1 + 0.5 * strength * np.sin((u + 1) * math.pi * n_folds + t * 1.2) * (0.3 + 0.7 * t)
    top_light = 1.04 - 0.08 * t
    return side * wave * top_light

# ---- 3. kain (skirt, ombak mengalun pleats on the right) ----
waist_y, hem_y = 980, 1760
skirt = scallop_poly([(470, waist_y), (730, waist_y), (930, hem_y)], hem_y, 270, 930, 14, 16)
garment(skirt, lambda: folds(470, 730, waist_y, hem_y, 4.5, 0.10, flare=1.5))
fold = Image.new("L", (W, H), 0); fd = ImageDraw.Draw(fold)
for k in range(4):
    x0 = 690 - k * 28
    fd.polygon([(x0, waist_y + 150), (x0 + 6, waist_y + 150), (x0 + 95 + k * 35, hem_y), (x0 + 50 + k * 35, hem_y)], fill=70)
fold = fold.filter(ImageFilter.GaussianBlur(9))
shadow = Image.new("RGBA", (W, H), (110, 80, 45, 0)); shadow.putalpha(fold)
canvas.alpha_composite(shadow)

# ---- 5. baju (long tunic to the knee, side panels flare) ----
body = scallop_poly([(500, 285), (560, 300), (600, 316), (640, 300), (700, 285),
                     (780, 335), (790, 640), (870, 1330)], 1330, 330, 870, 12, 18) + [(410, 640), (420, 335)]
garment(body, lambda: folds(400, 800, 300, 1330, 3.0, 0.08, flare=0.35))
# ---- 4. sleeves (lengan panjang lurus) ----
for sgn in (-1, 1):
    cx = 600
    sl = [(cx + sgn * 190, 330), (cx + sgn * 262, 352), (cx + sgn * 318, 1090), (cx + sgn * 205, 1105),
          (cx + sgn * 190, 620)]
    if sgn > 0: sl = sl[::-1]
    garment(sl, lambda: 0.94 * folds(600 + sgn * 190, 600 + sgn * 320, 330, 1100, 2.0, 0.07))
    # scalloped lace cuff
    cuff = scallop_poly([(cx + sgn * 205 - 2 * sgn, 1060), (cx + sgn * 318 + sgn * 2, 1050)],
                        1092, min(cx + sgn * 205, cx + sgn * 318), max(cx + sgn * 205, cx + sgn * 318), 4, 12)
    garment(cuff, lambda: np.full((H, W), 0.93, np.float32))

d = ImageDraw.Draw(canvas)
# neckline: round neck + short centre slit with pearl buttons
d.arc((520, 250, 680, 350), 20, 160, fill=(150, 118, 80, 200), width=4)
d.line([(600, 350), (600, 470)], fill=(150, 118, 80, 170), width=3)
for by in (380, 420, 460):
    d.ellipse((592, by - 8, 608, by + 8), fill=(252, 247, 236, 255), outline=(170, 140, 100, 255), width=2)
# kekek seam hints
for sgn in (-1, 1):
    d.line([(600 + sgn * 205, 650), (600 + sgn * 255, 1320)], fill=(150, 118, 80, 60), width=2)

# ---- 6. gentle sparkle on sequins ----
rng = np.random.default_rng(3)
alpha = np.asarray(canvas)[..., 3]
spark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(spark)
garment_mask = np.asarray(canvas.convert("L"))
for _ in range(260):
    x, y = int(rng.uniform(300, 900)), int(rng.uniform(300, 1760))
    pix = canvas.getpixel((x, y))
    if pix[0] < 235 and abs(pix[0] - pix[2]) > 25:  # on fabric, not background
        s = rng.uniform(2, 5); a = int(rng.uniform(120, 230))
        sd.line([(x - s * 2, y), (x + s * 2, y)], fill=(255, 250, 225, a), width=1)
        sd.line([(x, y - s * 2), (x, y + s * 2)], fill=(255, 250, 225, a), width=1)
        sd.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(255, 255, 240, a))
canvas.alpha_composite(spark.filter(ImageFilter.GaussianBlur(0.6)))

# ---- 7. title + swatch ----
d = ImageDraw.Draw(canvas)
d.text((W / 2, 110), "Baju Kurung Nikah", font=ImageFont.truetype(SERIF, 64), fill=(120, 88, 52, 255), anchor="mm")
d.text((W / 2, 175), "Lace sulam & labuci  •  Champagne gold", font=ImageFont.truetype(SANS, 32),
       fill=(150, 120, 85, 255), anchor="mm")
sw = photo.crop((600, 900, 900, 1200)).resize((170, 170))
sm = Image.new("L", (170, 170), 0); ImageDraw.Draw(sm).ellipse((0, 0, 169, 169), fill=255)
canvas.paste(sw, (980, 1640), sm)
d.ellipse((980, 1640, 1150, 1810), outline=(170, 140, 100, 255), width=4)
d.text((1065, 1835), "lace asal", font=ImageFont.truetype(SANS, 26), fill=(150, 120, 85, 255), anchor="mm")
canvas.convert("RGB").save(OUT, quality=95)
print("saved", OUT)
