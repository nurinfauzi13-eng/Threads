#!/usr/bin/env bash
# One-time setup for a fresh cloud session. Safe to re-run. All tools are free.
# Usage: bash video/setup.sh
set -e
export PATH="$HOME/.local/bin:$PATH"

echo "== Video-Use"
mkdir -p ~/Developer
test -d ~/Developer/video-use || git clone -q https://github.com/browser-use/video-use ~/Developer/video-use
(cd ~/Developer/video-use && uv sync -q)
mkdir -p ~/.claude/skills && ln -sfn ~/Developer/video-use ~/.claude/skills/video-use

echo "== yt-dlp"
command -v yt-dlp >/dev/null || uv tool install -q yt-dlp

echo "== HyperFrames (plugin + skills + CLI)"
claude plugin marketplace list 2>/dev/null | grep -q hyperframes || claude plugin marketplace add heygen-com/hyperframes
claude plugin list 2>/dev/null | grep -q "hyperframes@hyperframes" || claude plugin install hyperframes@hyperframes
npx --yes hyperframes skills update >/dev/null 2>&1 || true

echo "== Check"
node --version; ffmpeg -version | head -1; yt-dlp --version
npx --yes hyperframes --version
(cd ~/Developer/video-use && uv run -q python helpers/timeline_view.py --help >/dev/null && echo "video-use OK")
echo "Done. Whisper models download on first transcription (medium ≈ 1.5 GB)."
