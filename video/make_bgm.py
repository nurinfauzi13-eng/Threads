"""Synthesize an original, royalty-free chill lofi loop (no samples, no licences).

usage: python3 make_bgm.py OUT.wav SECONDS
"""
import sys, wave
import numpy as np

OUT, DUR = sys.argv[1], float(sys.argv[2])
SR, BPM = 44100, 84
beat = 60 / BPM
n = int(SR * DUR)
t = np.arange(n) / SR
mix = np.zeros(n)
rng = np.random.default_rng(7)

def midi(m): return 440 * 2 ** ((m - 69) / 12)

def ep(freq, start, length, vel=0.18):
    """Soft electric-piano note: sine + few harmonics, bell decay."""
    s, e = int(start * SR), min(n, int((start + length) * SR))
    if s >= n: return
    tt = np.arange(e - s) / SR
    env = np.exp(-tt * 1.8) * np.minimum(1, tt / 0.01)
    trem = 1 + 0.08 * np.sin(2 * np.pi * 4.5 * tt)
    sig = (np.sin(2*np.pi*freq*tt) + 0.35*np.sin(2*np.pi*2*freq*tt) * np.exp(-tt*4)
           + 0.12*np.sin(2*np.pi*3*freq*tt) * np.exp(-tt*6))
    mix[s:e] += vel * sig * env * trem

def kick(start, vel=0.5):
    s = int(start * SR); L = int(0.35 * SR); e = min(n, s + L)
    if s >= n: return
    tt = np.arange(e - s) / SR
    f = 50 + 70 * np.exp(-tt * 30)
    mix[s:e] += vel * np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-tt * 9)

def hat(start, vel=0.05):
    s = int(start * SR); L = int(0.06 * SR); e = min(n, s + L)
    if s >= n: return
    tt = np.arange(e - s) / SR
    noise = rng.standard_normal(e - s)
    noise = np.diff(np.concatenate([[0], noise]))  # crude high-pass
    mix[s:e] += vel * noise * np.exp(-tt * 60)

def snare(start, vel=0.12):
    s = int(start * SR); L = int(0.2 * SR); e = min(n, s + L)
    if s >= n: return
    tt = np.arange(e - s) / SR
    mix[s:e] += vel * (rng.standard_normal(e - s) * 0.7 + np.sin(2*np.pi*190*tt)) * np.exp(-tt * 18)

# ii-V-I-vi style progression in F major, one chord per bar (4 beats)
chords = [[62, 65, 69, 72], [67, 71, 74, 77], [65, 69, 72, 76], [62, 65, 69, 74]]
bass = [38, 43, 41, 38]
bar = 4 * beat
nbars = int(DUR / bar) + 1
for b in range(nbars):
    st = b * bar
    ch = chords[b % 4]
    for i, m in enumerate(ch):  # slightly strummed
        ep(midi(m), st + i * 0.018, bar * 1.1, 0.10)
    ep(midi(ch[-1] + 12), st + 2.5 * beat, beat * 1.5, 0.05)  # little melody hit
    ep(midi(bass[b % 4]), st, bar, 0.22)
    for k in range(4):
        bt = st + k * beat
        swing = 0.03 if k % 2 else 0
        if k in (0, 2): kick(bt)
        if k in (1, 3): snare(bt)
        hat(bt + swing); hat(bt + beat / 2 + 0.06, 0.03)

# lofi: low-pass (one-pole), vinyl crackle, gentle fade in/out
y = np.zeros(n); a = 0.18
for i in range(1, n): y[i] = y[i-1] + a * (mix[i] - y[i-1])
crackle = (rng.random(n) > 0.9993) * rng.standard_normal(n) * 0.15
y = y + crackle + rng.standard_normal(n) * 0.002
fade = np.minimum(1, np.minimum(t / 1.5, (DUR - t) / 2.0))
y *= np.clip(fade, 0, 1)
y = y / (np.abs(y).max() + 1e-9) * 0.8
pcm = (np.stack([y, y], 1) * 32767).astype(np.int16)
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("wrote", OUT)
