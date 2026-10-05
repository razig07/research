#!/usr/bin/env python3
"""Kokoro (free, local) voiceover: one cached WAV per scene part -> build/<ch>/vo.wav + timing.json."""
import json, sys, os, re, hashlib
import numpy as np, soundfile as sf
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ch = sys.argv[1]
spec = json.load(open(f'{V}/script/{ch}.json'))
B = f'{V}/build/{ch}'; os.makedirs(f'{B}/seg', exist_ok=True)
VOICE = os.environ.get('VOICE', 'bm_george'); SPEED = float(os.environ.get('SPEED', '0.95'))
SR = 24000; GAP = 0.35
PRON = json.load(open(f'{V}/tools/pron.json')) if os.path.exists(f'{V}/tools/pron.json') else {}
def prep(t):
    t = re.sub(r'[*~^]', '', t)
    for a, b in PRON.items(): t = re.sub(r'(?<![\w-])' + re.escape(a) + r'(?![\w-])', b, t)
    for a, b in [('%', ' percent'), ('&', ' and '), ('≈', ' about '), ('×', ' times '), ('→', ' to '), ('—', ', '), ('–', ' to ')]: t = t.replace(a, b)
    return re.sub(r'\s+', ' ', t).strip()
K = None; new = 0
def synth(text):
    global K, new
    t = prep(text); h = hashlib.md5(f'{VOICE}|{SPEED}|{t}'.encode()).hexdigest()[:16]; p = f'{B}/seg/{h}.wav'
    if os.path.exists(p): return sf.read(p, dtype='float32')[0]
    if K is None:
        from kokoro_onnx import Kokoro
        K = Kokoro(f'{V}/.models/kokoro-v1.0.onnx', f'{V}/.models/voices-v1.0.bin')
    a, sr = K.create(t, voice=VOICE, speed=SPEED, lang='en-gb'); a = np.asarray(a, dtype=np.float32)
    sf.write(p, a, SR); new += 1; return a
sil = lambda s: np.zeros(int(round(SR * s)), dtype=np.float32)
out, scenes, n = [], [], 0
for si, sc in enumerate(spec['scenes']):
    st = n / SR; parts = []
    texts = [sc['say'], None, sc['sayA']] if sc['type'] == 'quiz' else [sc.get('say', '')]
    for txt in texts:
        a = sil(float(sc.get('wait', 4.0))) if txt is None else (synth(txt) if txt.strip() else sil(1.2))
        parts.append({'start': round(n / SR, 3), 'end': round((n + len(a)) / SR, 3)}); out.append(a); n += len(a)
    pad = sil(GAP + (0.9 if sc['type'] == 'title' else 0) + float(sc.get('hold', 0))); out.append(pad); n += len(pad)
    scenes.append({'id': si, 'type': sc['type'], 'start': round(st, 3), 'dur': round(n / SR - st, 3), 'parts': parts})
sf.write(f'{B}/vo.wav', np.concatenate(out), SR, subtype='PCM_16')
json.dump({'total': round(n / SR, 3), 'scenes': scenes}, open(f'{B}/timing.json', 'w'))
print(f'TTS {ch}: {len(scenes)} scenes, {n/SR/60:.2f} min, {new} new segments')
