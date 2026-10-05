#!/bin/bash
# usage: tools/pipeline.sh ch01 [ch02 ...]   (serialized with flock; logs to out/pipeline.log)
cd /home/user/research/video
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
exec 9>/tmp/hf-pipeline.lock; flock 9
for ch in "$@"; do
  t0=$(date +%s); echo "== $ch start $(date +%T)"
  python3 tools/tts.py $ch || { echo "FAIL tts $ch"; continue; }; t1=$(date +%s)
  python3 tools/transcribe_for_hyperframes.py build/$ch/vo.wav --model small.en 2>&1 | grep -v Warning | tail -1; t2=$(date +%s)
  python3 tools/build.py $ch || { echo "FAIL build $ch"; continue; }
  (cd build/$ch && ../../node_modules/.bin/hyperframes render . -o ../../out/$ch.mp4 -f 24 --crf 27 -w 4 --quiet 2>&1 | tail -4); t3=$(date +%s)
  cp build/$ch/vo.srt out/$ch.srt 2>/dev/null
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/$ch.mp4 2>/dev/null); sz=$(du -m out/$ch.mp4 2>/dev/null | cut -f1)
  echo "DONE $ch video=${d}s size=${sz}MB tts=$((t1-t0))s whisper=$((t2-t1))s render=$((t3-t2))s"
done
