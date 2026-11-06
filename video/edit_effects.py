"""Skintific video v2: HD + captions + effects (zoom-through cuts, digital zoom
punch-ins, jump-cut pause removal, checklist pop-ins, glass CTA end card),
free CC0 SFX and an original synthesized lofi bed with voice ducking.

usage: python3 edit_effects.py SRC.mp4 MEDIA_DIR OUT.mp4 [--preview]
"""
import subprocess, sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, MEDIA, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PREVIEW = "--preview" in sys.argv
W, H, FPS = 1080, 1920, 30
SRC_DUR = 39.566
BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
SYM = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
YEL = (255, 214, 10)
WHITE = (255, 255, 255)
INK = (17, 17, 24)

# ---------- edit decisions (source seconds) ----------
KEEP = [(0.90, 22.55), (23.35, 29.00), (30.10, 35.50), (36.40, SRC_DUR)]  # drop dead air
SCENES = [3.467, 7.4, 11.4, 17.1, 21.333, 25.9, 35.1]                   # zoom-through cuts
PUNCH = [  # digital zoom punch-ins: (start, end, peak zoom)
    (9.45, 10.0, 1.08), (10.0, 10.9, 1.06), (17.4, 19.4, 1.10),
    (31.9, 32.75, 1.07), (33.9, 35.5, 1.09), (38.2, 39.5, 1.06),
]
CHUNKS = [
    (1.15, 2.20, "Hai, guys!"), (2.20, 4.45, "Setakat ni, em..."),
    (5.15, 6.70, "Skintific"), (6.70, 10.00, "brand memang best."),
    (10.00, 12.70, "Gila! Pakai dekat"), (12.70, 15.50, "your lips and then"),
    (15.50, 16.80, "your lips are going"), (16.80, 19.40, "to plump like that."),
    (19.50, 22.40, "Not only that,"), (23.40, 25.60, "it's best to use"),
    (25.60, 28.90, "this lip balm."), (30.20, 31.70, "Stick? No,"),
    (31.70, 32.75, "it's not lipstick,"), (32.75, 35.50, "it's, um, lip gloss."),
    (36.45, 37.70, "Lip gloss, eh,"), (37.75, 39.60, "uh, something. Ah."),
]
CHECKS = [(31.75, "Lipstick", False), (33.95, "Lip gloss", True)]  # checklist pop-ins
CTA_LEN = 2.6

def src_to_out(ts):
    acc = 0.0
    for a, b in KEEP:
        if ts < a: return None
        if ts <= b: return acc + ts - a
        acc += b - a
    return None

OUT_MAIN = sum(b - a for a, b in KEEP)
TOTAL = OUT_MAIN + CTA_LEN

def ease(x): x = max(0., min(1., x)); return x * x * (3 - 2 * x)

# ---------- caption card (covers old burned-in captions) ----------
CX, CW, CY, CH = 540, 820, 1312, 160
OLD_BAND = (150, 1318, 930, 1468)   # region of old captions in 1080 space
_cache = {}
def caption_card(txt, active):
    key = (txt, active)
    if key in _cache: return _cache[key]
    words = txt.split(" "); size = 70
    while True:
        f = ImageFont.truetype(BOLD, size); sp = f.getlength(" ")
        ws = [f.getlength(w) for w in words]; tot = sum(ws) + sp * (len(words) - 1)
        if tot <= CW - 90 or size <= 40: break
        size -= 2
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, CW - 1, CH - 1), radius=38, fill=INK + (255,))
    d.rounded_rectangle((0, 0, 14, CH - 1), radius=7, fill=YEL + (255,))
    asc, desc = f.getmetrics(); x = (CW - tot) / 2; y = (CH - asc - desc) / 2
    for i, (w, wd) in enumerate(zip(words, ws)):
        if i == active:
            d.rounded_rectangle((x - 10, y - 4, x + wd + 10, y + asc + desc + 2), radius=14,
                                fill=(64, 56, 20, 255))
        d.text((x, y), w, font=f, fill=(YEL if i == active else WHITE) + (255,))
        x += wd + sp
    _cache[key] = np.array(im); return _cache[key]

def chunk_at(ts):
    for s, e, txt in CHUNKS:
        if s <= ts < e:
            n = len(txt.split()); return s, txt, min(n - 1, int((ts - s) / (e - s) * n))
    return None

def check_tag(label, ok):
    f = ImageFont.truetype(BOLD, 54); fs = ImageFont.truetype(SYM, 54)
    tw = f.getlength(label); w, h = int(tw + 150), 96
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=48, fill=(255, 255, 255, 235))
    col = (22, 163, 74) if ok else (220, 38, 38)
    d.ellipse((14, 14, 82, 82), fill=col + (255,))
    d.text((48, 47), "✓" if ok else "✗", font=fs, fill=WHITE + (255,), anchor="mm")
    d.text((100, 48), label, font=f, fill=INK + (255,), anchor="lm")
    if not ok:  # strike-through
        d.line((100, 50, 100 + tw, 50), fill=col + (255,), width=6)
    return np.array(im)
TAGS = [(s, check_tag(l, ok)) for s, l, ok in CHECKS]

def paste(fr, rgba, x0, y0, alpha=1.0):
    h, w = rgba.shape[:2]
    x1, y1 = max(0, x0), max(0, y0); x2, y2 = min(W, x0 + w), min(H, y0 + h)
    if x2 <= x1 or y2 <= y1: return
    sub = rgba[y1 - y0:y2 - y0, x1 - x0:x2 - x0]
    a = sub[..., 3:4].astype(np.float32) / 255 * alpha
    roi = fr[y1:y2, x1:x2].astype(np.float32)
    fr[y1:y2, x1:x2] = (sub[..., :3] * a + roi * (1 - a)).astype(np.uint8)

# ---------- per-frame camera: zoom + blur ----------
AX, AY = 540, 1392  # zoom anchor = caption centre, keeps the cover aligned
def camera(ts):
    z, blur = 1.0, 0.0
    o = src_to_out(ts) or 0
    if o < 0.6:  # hook: slam-in from 1.3 with blur
        k = ease(o / 0.6); z = 1.3 - 0.3 * k; blur = (1 - k) * 14
    for sc in SCENES:  # zoom-through
        d = ts - sc
        if -0.17 <= d < 0: k = ease((d + 0.17) / 0.17); z *= 1 + 0.28 * k; blur = max(blur, 16 * k)
        elif 0 <= d < 0.2: k = 1 - ease(d / 0.2); z *= 1 + 0.28 * k; blur = max(blur, 16 * k)
    for s, e, pk in PUNCH:
        if s <= ts < e:
            k = ease((ts - s) / 0.12) * (1 - ease((ts - (e - 0.15)) / 0.15)); z *= 1 + (pk - 1) * k
    # jump-cuts: alternate framing so the cut reads as intentional
    for i, (a, b) in enumerate(KEEP):
        if a <= ts <= b and i % 2 == 1: z *= 1.05
    return z, blur

def apply_camera(img, z, blur):
    if z != 1.0:
        nw, nh = int(W * z), int(H * z)
        big = img.resize((nw, nh), Image.BILINEAR if blur > 2 else Image.LANCZOS)
        x0 = int(AX * z - AX); y0 = int(AY * z - AY)
        img = big.crop((x0, y0, x0 + W, y0 + H))
    if blur > 0.5: img = img.filter(ImageFilter.GaussianBlur(blur))
    return img

# ---------- glass CTA end card ----------
def cta_frame(last, k):
    bg = last.filter(ImageFilter.GaussianBlur(4 + 22 * ease(k * 3)))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (10, 10, 14)), 0.35 * ease(k * 3))
    fr = bg.convert("RGBA")
    pk = ease((k - 0.05) * 4)
    pw, ph = 860, 560; px, py = (W - pw) // 2, 640 + int((1 - pk) * 80)
    region = bg.crop((px, py, px + pw, py + ph)).filter(ImageFilter.GaussianBlur(30))
    region = Image.blend(region, Image.new("RGB", (pw, ph), (255, 255, 255)), 0.18)
    mask = Image.new("L", (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw - 1, ph - 1), 56, fill=int(255 * pk))
    fr.paste(region, (px, py), mask)
    d = ImageDraw.Draw(fr)
    d.rounded_rectangle((px, py, px + pw - 1, py + ph - 1), 56, outline=(255, 255, 255, int(110 * pk)), width=3)
    a = int(255 * pk)
    f1 = ImageFont.truetype(SEMI, 50); f2 = ImageFont.truetype(BOLD, 104); f3 = ImageFont.truetype(BOLD, 56)
    d.text((W / 2, py + 105), "Skintific", font=f1, fill=WHITE + (a,), anchor="mm")
    d.text((W / 2, py + 215), "Lip Gloss", font=f2, fill=YEL + (a,), anchor="mm")
    bk = ease((k - 0.3) * 4); pulse = 1 + 0.035 * math.sin(k * CTA_LEN * 7) * bk
    bw, bh = 680 * pulse, 130 * pulse; by = py + 400
    d.rounded_rectangle((W / 2 - bw / 2, by - bh / 2, W / 2 + bw / 2, by + bh / 2), 65, fill=YEL + (int(255 * bk),))
    d.text((W / 2, by), "Tekan beg kuning!", font=f3, fill=INK + (int(255 * bk),), anchor="mm")
    return np.array(fr.convert("RGB"))

# ---------- audio ----------
def build_audio(path):
    parts, labels = [], []
    for i, (a, b) in enumerate(KEEP):
        parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,"
                     f"afade=t=out:st={b - a - 0.03:.3f}:d=0.03[v{i}]")
        labels.append(f"[v{i}]")
    fc = ";".join(parts) + f";{''.join(labels)}concat=n={len(KEEP)}:v=0:a=1,"
    fc += f"apad=pad_dur={CTA_LEN},loudnorm=I=-15:TP=-2:LRA=9,asplit=2[voice][sc]"
    # sfx timeline (output seconds)
    sfx = [("whoosh_cc0.mp3", 0.0, 0.55)]
    for i, sc in enumerate(SCENES):
        o = src_to_out(sc)
        if o is not None: sfx.append(("whoosh_cc0.mp3" if i % 2 == 0 else "click.mp3", max(0, o - 0.2), 0.32 if i % 2 == 0 else 0.6))
    for s, e, pk in PUNCH:
        o = src_to_out(s)
        if o is not None: sfx.append(("click.mp3", o, 0.55))
    for s, _, _ in CHECKS:
        sfx.append(("click.mp3", src_to_out(s), 0.8))
    sfx.append(("shimmer.mp3", OUT_MAIN + 0.1, 0.35))
    inputs = ["-i", SRC, "-i", os.path.join(MEDIA, "bgm.wav")]
    for j, (f, at, vol) in enumerate(sfx):
        inputs += ["-i", os.path.join(MEDIA, f)]
        fc += (f";[{j + 2}:a]atrim=0:1.6,aformat=sample_rates=48000:channel_layouts=stereo,"
               f"volume={vol},adelay={int(at * 1000)}|{int(at * 1000)}[s{j}]")
    fc += (f";[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.20,"
           f"atrim=0:{TOTAL:.2f}[bgm0]")
    fc += ";[sc]aformat=sample_rates=48000:channel_layouts=stereo[scs]"
    fc += ";[bgm0][scs]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[bgm]"
    fc += ";[voice]aformat=sample_rates=48000:channel_layouts=stereo[vo]"
    allm = "[vo][bgm]" + "".join(f"[s{j}]" for j in range(len(sfx)))
    fc += f";{allm}amix=inputs={len(sfx) + 2}:normalize=0:duration=first,alimiter=limit=0.89[aout]"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", fc,
                    "-map", "[aout]", "-t", f"{TOTAL:.2f}", "-c:a", "pcm_s16le", path], check=True)

# ---------- main ----------
bgm = os.path.join(MEDIA, "bgm.wav")
if not os.path.exists(bgm):
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "make_bgm.py"),
                    bgm, str(TOTAL + 1)], check=True)
audio_tmp = OUT + ".audio.wav"
build_audio(audio_tmp)

vf = "scale=1080:1920:flags=lanczos" if PREVIEW else \
     "hqdn3d=1.5:1.5:4:4,scale=1080:1920:flags=lanczos,unsharp=5:5:0.8:3:3:0.3,eq=contrast=1.04:saturation=1.08"
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", SRC, "-vf", vf, "-r", str(FPS),
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio_tmp,
    "-c:v", "libx264", "-preset", "veryfast" if PREVIEW else "slow", "-crf", "23" if PREVIEW else "17",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT],
    stdin=subprocess.PIPE)

fs = W * H * 3; i = 0; last = None
x1, y1, x2, y2 = OLD_BAND
while True:
    buf = dec.stdout.read(fs)
    if len(buf) < fs: break
    ts = i / FPS; i += 1
    if src_to_out(ts) is None: continue
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
    ch = chunk_at(ts)
    if ch:  # smear old captions before any zoom so nothing readable can leak
        band = Image.fromarray(fr[y1:y2, x1:x2]).filter(ImageFilter.GaussianBlur(18))
        fr[y1:y2, x1:x2] = np.array(band)
    z, bl = camera(ts)
    img = apply_camera(Image.fromarray(fr), z, bl)
    fr = np.array(img)
    last = img  # clean frame (no caption card) for the end card
    if ch:
        s, txt, act = ch
        pop = min(1.0, (ts - s) / 0.12)
        card = caption_card(txt, act)
        paste(fr, card, CX - CW // 2, CY + int((1 - pop) * 18))
    for s, tag in TAGS:
        if s <= ts < 35.5:
            k = ease((ts - s) / 0.18)
            paste(fr, tag, W - 60 - tag.shape[1] + int((1 - k) * 60), 700 + (0 if tag is TAGS[0][1] else 120), k)
    enc.stdin.write(fr.tobytes())
for j in range(int(CTA_LEN * FPS)):
    enc.stdin.write(cta_frame(last, j / (CTA_LEN * FPS)).tobytes())
enc.stdin.close(); enc.wait(); os.remove(audio_tmp)
print(f"done {OUT}  duration≈{TOTAL:.1f}s")
