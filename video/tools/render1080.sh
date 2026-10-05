#!/bin/bash
# Re-render chapters at 1920x1080 (layout scaled 1.5x, vector-sharp). Reuses cached TTS + whisper timing.
cd /home/user/research/video
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
mkdir -p out1080; exec 9>/tmp/hf-pipeline.lock; flock 9
for ch in "$@"; do
  t0=$(date +%s); SCALE=1.5 python3 tools/build.py $ch >/dev/null || { echo "FAIL build $ch"; continue; }
  (cd build/$ch && ../../node_modules/.bin/hyperframes render . -o ../../out1080/$ch.mp4 -f 24 --crf 24 -w 4 --quiet 2>&1 | grep -iE "error|fail" | tail -2)
  cp out/$ch.srt out1080/ 2>/dev/null; echo "DONE $ch $(du -m out1080/$ch.mp4 | cut -f1)MB render=$(( $(date +%s)-t0 ))s"
done
