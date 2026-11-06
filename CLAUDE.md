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
