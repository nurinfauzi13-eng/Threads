"""HD upscale + new animated captions that cover the old burned-in captions.

usage: python3 edit_captions.py SRC.mp4 OUT.mp4
"""
import subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

# (start, end, text). Word highlight timing is spread evenly inside each chunk.
CHUNKS = [
    (1.15, 2.20, "Hai, guys!"),
    (2.20, 4.45, "Setakat ni, em..."),
    (5.15, 6.70, "Skintific"),
    (6.70, 10.00, "brand memang best."),
    (10.00, 12.70, "Gila! Pakai dekat"),
    (12.70, 15.50, "your lips and then"),
    (15.50, 16.80, "your lips are going"),
    (16.80, 19.40, "to plump like that."),
    (19.50, 22.40, "Not only that,"),
    (23.40, 25.60, "it's best to use"),
    (25.60, 28.90, "this lip balm."),
    (30.20, 31.70, "Stick? No,"),
    (31.70, 32.75, "it's not lipstick,"),
    (32.75, 35.50, "it's, um, lip gloss."),
    (36.45, 37.70, "Lip gloss, eh,"),
    (37.75, 39.60, "uh, something. Ah."),
]

# Card covers the old caption strip (source x 95-490, y 712-772, scaled x1.875)
CX, CW, CY, CH = 540, 800, 1312, 160
CARD = (17, 17, 24)
TEXT = (255, 255, 255)
HL = (255, 214, 10)

def build_card(text, active, t_in):
    words = text.split(" ")
    size = 70
    while True:
        f = ImageFont.truetype(FONT, size)
        sp = f.getlength(" ")
        widths = [f.getlength(w) for w in words]
        total = sum(widths) + sp * (len(words) - 1)
        if total <= CW - 90 or size <= 40: break
        size -= 2
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, CW - 1, CH - 1), radius=38, fill=CARD + (255,))
    d.rounded_rectangle((0, 0, 14, CH - 1), radius=7, fill=HL + (255,))  # accent bar
    x = (CW - total) / 2
    asc, desc = f.getmetrics()
    y = (CH - (asc + desc)) / 2
    for i, (w, wd) in enumerate(zip(words, widths)):
        col = HL if i == active else TEXT
        if i == active:
            d.rounded_rectangle((x - 10, y - 4, x + wd + 10, y + asc + desc + 2), radius=14,
                                fill=(64, 56, 20, 255))
        d.text((x, y), w, font=f, fill=col + (255,))
        x += wd + sp
    return im

cache = {}
def overlay_for(t):
    for s, e, txt in CHUNKS:
        if s <= t < e:
            n = len(txt.split(" "))
            active = min(n - 1, int((t - s) / (e - s) * n))
            key = (txt, active)
            if key not in cache:
                cache[key] = np.array(build_card(txt, active, s))
            pop = min(1.0, (t - s) / 0.12)  # quick pop-in
            return cache[key], pop
    return None, 0

dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", SRC, "-vf",
    "hqdn3d=1.5:1.5:4:4,scale=1080:1920:flags=lanczos,unsharp=5:5:0.8:3:3:0.3,"
    "eq=contrast=1.04:saturation=1.08", "-r", str(FPS),
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", SRC, "-map", "0:v", "-map", "1:a",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high",
    "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
    "-shortest", OUT], stdin=subprocess.PIPE)

n = 0
fsize = W * H * 3
while True:
    buf = dec.stdout.read(fsize)
    if len(buf) < fsize: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
    card, pop = overlay_for(n / FPS)
    if card is not None:
        ch, cw = card.shape[:2]
        x0, y0 = CX - cw // 2, CY + int((1 - pop) * 18)
        a = card[..., 3:4].astype(np.float32) / 255
        roi = fr[y0:y0 + ch, x0:x0 + cw].astype(np.float32)
        fr[y0:y0 + ch, x0:x0 + cw] = (card[..., :3] * a + roi * (1 - a)).astype(np.uint8)
    enc.stdin.write(fr.tobytes())
    n += 1
enc.stdin.close(); enc.wait()
print("frames", n, "->", OUT)
