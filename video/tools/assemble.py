#!/usr/bin/env python3
"""Join chapter MP4s into out/full.mp4 with chapter markers and a soft subtitle track."""
import json, subprocess, os, sys
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); O = f'{V}/out'
A, Z, NAME = (int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]) if len(sys.argv) > 3 else (0, 10, 'full')
chs = [f'ch{i:02d}' for i in range(A, Z + 1) if os.path.exists(f'{O}/ch{i:02d}.mp4')]
durs = [float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f'{O}/{c}.mp4']).decode()) for c in chs]
labels = [json.load(open(f'{V}/script/{c}.json'))['label'] for c in chs]
open(f'{O}/concat_{NAME}.txt', 'w').write(''.join(f"file '{O}/{c}.mp4'\n" for c in chs))
meta, yt, t = [';FFMETADATA1', 'title=Break the fantasy loop, then build skill'], [], 0.0
for lab, d in zip(labels, durs):
    meta += ['[CHAPTER]', 'TIMEBASE=1/1000', f'START={int(t * 1000)}', f'END={int((t + d) * 1000)}', f'title={lab}']
    yt.append(f'{int(t // 3600)}:{int(t % 3600 // 60):02}:{int(t % 60):02} {lab}' if t >= 3600 else f'{int(t // 60)}:{int(t % 60):02} {lab}'); t += d
open(f'{O}/chapters_{NAME}.txt', 'w').write('\n'.join(meta) + '\n'); open(f'{O}/{NAME}_timestamps.txt', 'w').write('\n'.join(yt) + '\n')
def p(s): h, m, r = s.split(':'); sec, ms = r.split(','); return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000
def f(x): return f'{int(x // 3600):02}:{int(x % 3600 // 60):02}:{int(x % 60):02},{int(round(x % 1 * 1000)) % 1000:03}'
subs, n, off = [], 1, 0.0
for c, d in zip(chs, durs):
    if os.path.exists(f'{O}/{c}.srt'):
        for b in open(f'{O}/{c}.srt').read().strip().split('\n\n'):
            L = b.split('\n')
            if len(L) < 3: continue
            a, z = L[1].split(' --> '); subs.append(f'{n}\n{f(p(a) + off)} --> {f(p(z) + off)}\n' + '\n'.join(L[2:])); n += 1
    off += d
open(f'{O}/{NAME}.srt', 'w').write('\n\n'.join(subs) + '\n')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{O}/concat_{NAME}.txt', '-i', f'{O}/chapters_{NAME}.txt', '-i', f'{O}/{NAME}.srt',
                '-map', '0:v', '-map', '0:a', '-map', '2:s', '-map_metadata', '1', '-map_chapters', '1', '-c:v', 'copy', '-c:a', 'copy', '-c:s', 'mov_text',
                '-metadata:s:s:0', 'language=eng', '-movflags', '+faststart', f'{O}/{NAME}.mp4'], check=True)
sz = os.path.getsize(f'{O}/{NAME}.mp4') / 1e6
print(f'ASSEMBLED {len(chs)} chapters, {t / 60:.1f} min, {sz:.0f} MB'); print('\n'.join(yt))
