# Video editing — FREE TOOLS ONLY

The owner wants zero spending. Never use a paid service, API credits, or a paid plan.
Don't sign in to anything that could bill, and ask before anything that needs an account.

| Need | Use (free) | Do NOT use |
|---|---|---|
| Transcription | `npx hyperframes transcribe <file> --engine whisper --model small --language ms` (local whisper.cpp; use `medium` for better Malay) | ElevenLabs, `--engine heygen` |
| Motion graphics / render | HyperFrames CLI (`npx hyperframes ...`), Remotion (free for individuals) | HyperFrames Studio Pro, HeyGen generate |
| Sound effects | `npx hyperframes media-use resolve --type sfx --intent "..."` (Openverse CC0 / bundled). Prefer CC0; if CC BY, put the credit in the post caption | HeyGen SFX |
| Background music | Openverse CC0 tracks: `https://api.openverse.org/v1/audio/?q=<mood>&license=cc0`, then `media-use resolve --type bgm --adopt --from <url>`; or the owner adds a trending sound in the TikTok/IG app | HeyGen music catalog, MusicGen-paid, any stock site |
| Voiceover (if ever needed) | `npx hyperframes tts` (Kokoro, on-device) | HeyGen voices, ElevenLabs |
| Download reference videos | `yt-dlp` | — |
| Cutting / grading / subtitles | Video-Use helpers + ffmpeg (skip its ElevenLabs `transcribe.py`; feed it the whisper transcript instead) | — |

Output format: 9:16, 1080x1920, respect TikTok/IG safe zones.

## New session? Run setup first
Cloud sessions start empty. Before any video work run: `bash video/setup.sh`
(installs Video-Use, yt-dlp, HyperFrames plugin/skills/CLI; idempotent). Node 22, Python/uv, git, ffmpeg are preinstalled.

## Owner's preferences
- Language: Malay mixed with English (Manglish). Captions keep the words as spoken.
- Affiliate content (TikTok Shop / Shopee). CTA = "Tekan beg kuning!" (yellow basket).
- Always show a preview before the final render. Make each design different from the previous video.
- Don't cover faces or the product. Background music must never drown the voice.
- Commit and push finished videos + scripts to `master`.

## Proven workflow (see scripts in `video/`)
1. Probe: `ffprobe`, frame grid, `scdet` for scene cuts, per-0.5s RMS to find speech/pauses.
2. Transcribe free with whisper `--model medium`. Whisper is weak on Manglish: `--language ms`
   forces formal Malay, auto mode translates to English. If the clip already has burned-in
   captions, read them from frames (tile the caption band every 0.25s) — they are the best transcript.
   Ask the owner to confirm any section you had to guess.
3. Burned-in old captions can't be removed (delogo smears). Cover them with an opaque caption
   card exactly over that band, chunks back-to-back (no gaps), then scan every frame to prove nothing leaks.
4. Free SFX via `media-use resolve --type sfx` (CC0). freesound.org CDN blocks direct downloads.
   Music: `video/make_bgm.py` synthesizes an original lofi bed (no copyright), sidechain-ducked under voice.
5. Scripts: `make_video.py` (product promo from images), `edit_captions.py` (HD + captions),
   `edit_effects.py` (HD + captions + zoom-through cuts, punch-ins, pause cuts, checklist, glass CTA, audio mix).
   Edit the decision lists at the top (KEEP, SCENES, PUNCH, CHUNKS, CHECKS) for a new clip.
