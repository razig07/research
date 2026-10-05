#!/usr/bin/env python3
"""Validate questions, inline data + fonts into site/app.html -> site/dist/index.html, zip site/dist -> learning_site.zip."""
import json, os, base64, zipfile, re
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); S = f'{V}/site'; DIST = f'{S}/dist'
LJ = json.load(open(f'{S}/lessons.json')); QJ = json.load(open(f'{S}/questions.json'))
lessons = LJ['lessons']; LI = {l['id']: l for l in lessons}
smap = {l['id']: {s['i']: s['t'] for s in l['scenes']} for l in lessons}
qs, cnt, errs = [], {}, []
for q in QJ:
    l = q['l']
    if l not in LI: errs.append(f'unknown lesson {l}'); continue
    if q['s'] not in smap[l]: errs.append(f'{l}: scene {q["s"]} not in lesson'); continue
    t = q['t']; need = {'mc': ['o', 'a'], 'tf': ['a'], 'type': ['a'], 'order': ['o'], 'num': ['a', 'tol', 'min', 'max'], 'recall': ['a']}[t]
    if any(k not in q for k in need): errs.append(f'{l}: missing fields in {q["q"][:30]}'); continue
    if t == 'mc' and not (0 <= q['a'] < len(q['o'])): errs.append(f'{l}: bad mc answer')
    if t == 'num' and not (q['min'] <= q['a'] <= q['max']): errs.append(f'{l}: num answer out of range')
    cnt[l] = cnt.get(l, 0) + 1; q = dict(q); q['id'] = f'{l}.{cnt[l]}'; q['ts'] = smap[l][q.pop('s')]; qs.append(q)
for z in LJ['quizzes']:
    c, i = z['ch'], z['i']; k = [p.strip() for p in z['a'].split('·')] if '·' in z['a'] else [z['a']]
    q = {'t': 'recall', 'q': z['q'], 'a': z['full'], 'k': k, 'ts': None}
    if c == 10: q.update(l='L44', fin=True, id=f'R{i}')
    elif i == 1 and c >= 2: q.update(l=[l for l in lessons if l['ch'] == c - 1][-1]['id'], w=c, id=f'W{c}')
    else:
        cand = [l for l in lessons if l['ch'] == c and min(s['i'] for s in l['scenes']) < i]
        q.update(l=max(cand, key=lambda l: max(s['i'] for s in l['scenes']))['id'], id=f'V{c}.{i}')
    cnt[q['l']] = cnt.get(q['l'], 0) + 1; qs.append(q)
low = [l['id'] for l in lessons if cnt.get(l['id'], 0) < 2]
if errs or low: raise SystemExit('VALIDATION FAILED: ' + '; '.join(errs + [f'{x} has <2 questions' for x in low]))
NM = f'{V}/node_modules/@fontsource'
def ff(fam, w, p): return f"@font-face{{font-family:{fam};font-weight:{w};font-display:swap;src:url(data:font/woff2;base64,{base64.b64encode(open(f'{NM}/{p}', 'rb').read()).decode()}) format('woff2')}}"
fonts = ff('Caveat', 700, 'caveat/files/caveat-latin-700-normal.woff2') + ff('Inter', 400, 'inter/files/inter-latin-400-normal.woff2') + ff('Inter', 600, 'inter/files/inter-latin-600-normal.woff2')
data = {'chapters': LJ['chapters'], 'lessons': [{'id': l['id'], 'ch': l['ch'], 'title': l['title'], 'dur': l['dur'], 'scenes': [{'t': s['t'], 'n': s['n']} for s in l['scenes']], 'cues': l['cues']} for l in lessons], 'qs': qs}
html = open(f'{S}/app.html').read().replace('/*FONTS*/', fonts).replace('/*DATA*/', json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
open(f'{DIST}/index.html', 'w').write(html)
open(f'{DIST}/README.txt', 'w').write('Open index.html in Chrome, Edge, Safari or Firefox. Keep the clips and posters folders next to it.\nYour progress is saved in that browser. Use Stats > Back up progress now and then.\n')
zp = f'{V}/learning_site.zip'
with zipfile.ZipFile(zp, 'w') as z:
    for root, _, files in os.walk(DIST):
        for f in sorted(files):
            p = os.path.join(root, f); z.write(p, 'learning_site/' + os.path.relpath(p, DIST), compress_type=zipfile.ZIP_DEFLATED if f.endswith(('.html', '.txt')) else zipfile.ZIP_STORED)
print(f'BUILD OK: {len(lessons)} lessons, {len(qs)} questions (min per lesson {min(cnt.values())}), index.html {len(html) / 1e3:.0f} KB, zip {os.path.getsize(zp) / 1e6:.0f} MB')
