#!/usr/bin/env python3
"""dma-transcribe-for-hyperframes: word-level timestamps (faster-whisper) -> <name>.words.json, <name>.timing.html, <name>.srt"""
import argparse, json, os, html
from faster_whisper import WhisperModel
ap = argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--model', default='medium'); ap.add_argument('--language', default='en')
a = ap.parse_args()
m = WhisperModel(a.model, device='cpu', compute_type='int8', download_root=os.environ.get('WHISPER_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.models', 'whisper')))
segs, info = m.transcribe(a.input, language=a.language, word_timestamps=True, beam_size=5, condition_on_previous_text=False)
words, segments = [], []
for s in segs:
    segments.append({'start': round(s.start, 3), 'end': round(s.end, 3), 'text': s.text.strip()})
    for w in (s.words or []): words.append({'word': w.word.strip(), 'start': round(w.start, 3), 'end': round(w.end, 3), 'prob': round(w.probability, 3)})
base = os.path.splitext(a.input)[0]
json.dump({'source': os.path.basename(a.input), 'model': a.model, 'duration': round(info.duration, 3), 'words': words, 'segments': segments}, open(base + '.words.json', 'w'), indent=1)
def ts(t): h, r = divmod(t, 3600); mi, s = divmod(r, 60); return f'{int(h):02}:{int(mi):02}:{int(s):02},{int(round((s % 1) * 1000)) % 1000:03}'
lines, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) >= 9 or w['word'].endswith(('.', '?', '!')): lines.append(cur); cur = []
if cur: lines.append(cur)
with open(base + '.srt', 'w') as f:
    for i, l in enumerate(lines, 1): f.write(f"{i}\n{ts(l[0]['start'])} --> {ts(l[-1]['end'])}\n{' '.join(w['word'] for w in l)}\n\n")
with open(base + '.timing.html', 'w') as f:
    f.write('<!doctype html><meta charset="utf-8"><title>Timing</title><style>body{font:16px/2 system-ui;max-width:900px;margin:30px auto}span{padding:2px 3px;border-radius:4px;cursor:default}span:hover{background:#ffe08a}</style><h3>' + html.escape(os.path.basename(a.input)) + '</h3><p>')
    f.write(' '.join(f'<span title="{w["start"]:.3f} – {w["end"]:.3f}s">{html.escape(w["word"])}</span>' for w in words) + '</p>')
print(f'WHISPER {len(words)} words, {info.duration:.1f}s -> {base}.words.json / .timing.html / .srt')
