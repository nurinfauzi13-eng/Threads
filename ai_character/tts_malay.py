"""Malay text-to-speech on CPU with Meta MMS-TTS (facebook/mms-tts-zlm, free/open).
usage: python tts_malay.py "teks" out.wav [speed]"""
import sys, torch, numpy as np, soundfile as sf
from transformers import VitsModel, AutoTokenizer
text, out = sys.argv[1], sys.argv[2]
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.1
tok = AutoTokenizer.from_pretrained("facebook/mms-tts-zlm")
model = VitsModel.from_pretrained("facebook/mms-tts-zlm")
model.speaking_rate = speed; model.noise_scale = 0.75
torch.manual_seed(0)
with torch.no_grad():
    wav = model(**tok(text.lower(), return_tensors="pt")).waveform[0].numpy()
sf.write(out, wav / (np.abs(wav).max() + 1e-9) * 0.9, model.config.sampling_rate)
print("saved", out, len(wav) / model.config.sampling_rate, "s")
