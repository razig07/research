#!/usr/bin/env python3
"""script/<ch>.json + build/<ch>/timing.json (TTS) + vo.words.json (whisper) -> build/<ch>/index.html (HyperFrames composition)."""
import json, re, sys, os, shutil, difflib, html, math
from collections import defaultdict
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ch = sys.argv[1]; spec = json.load(open(f'{V}/script/{ch}.json')); B = f'{V}/build/{ch}'
TM = json.load(open(f'{B}/timing.json'))
W = json.load(open(f'{B}/vo.words.json'))['words'] if os.path.exists(f'{B}/vo.words.json') else []
COL = {'ink': '#23262F', 'mute': '#6B6558', 'teal': '#1F8A84', 'coral': '#D65A45', 'amber': '#C98A12', 'blue': '#3B6EA8'}
def col(c, d='ink'): c = c or d; return COL.get(c, c)
def tint(c, a='1f'): c = col(c); return c + a if c.startswith('#') and len(c) == 7 else c
STOP = set("the a an and or of to in on for with is are was were be been it its this that these those as at by from your you we our i not no but if so do does did can will just than then into about over more most less very their they them he she his her who what when how why one two it's that's".split())
def norm(s): return [w for w in re.split(r"[^a-z0-9']+", str(s).lower().replace('’', "'")) if w.strip("'")]
def clean(t): return re.sub(r'[*~^]', '', str(t))
esc = lambda s: html.escape(str(s), quote=True)
def fs(n, steps):
    for lim, size in steps:
        if n <= lim: return size
    return steps[-1][1]
def ptexts(sc): return [sc['say'], '', sc['sayA']] if sc['type'] == 'quiz' else [sc.get('say', '')]
# ---- align script words to whisper words (difflib); fallback = proportional inside each TTS part ----
stoks, owner = [], []
for si, sc in enumerate(spec['scenes']):
    for pi, txt in enumerate(ptexts(sc)):
        for w in norm(clean(txt)): stoks.append(w); owner.append((si, pi))
wt, wtime = [], []
for w in W:
    for tk in norm(w['word']): wt.append(tk); wtime.append(w['start'])
T = [None] * len(stoks)
for a, b, n in difflib.SequenceMatcher(None, stoks, wt, autojunk=False).get_matching_blocks():
    for i in range(n): T[a + i] = wtime[b + i]
groups = defaultdict(list)
for i, o in enumerate(owner): groups[o].append(i)
TT = [0.0] * len(stoks); good = 0
for (si, pi), idx in groups.items():
    p = TM['scenes'][si]['parts'][pi]; ps, pe = p['start'], p['end']
    for m, i in enumerate(idx):
        t = T[i]
        if t is not None and ps - 0.4 <= t <= pe + 0.4: TT[i] = t; good += 1
        else: TT[i] = ps + (pe - ps) * m / max(len(idx), 1)
class Sc:
    def __init__(s, si, sc):
        tm = TM['scenes'][si]; s.si, s.sc, s.st, s.du, s.parts = si, sc, tm['start'], tm['dur'], tm['parts']; s.en = s.st + s.du
        s.tok = [(stoks[i], TT[i], owner[i][1]) for i in range(len(stoks)) if owner[i][0] == si]; s.ptr = 0; s.html = []; s.shapes = []; s.miss = 0
    def find(s, text, part=0, frm=None, adv=True):
        if not text: return None
        c = [w for w in norm(clean(text)) if w not in STOP and len(w) > 2] or norm(clean(text))
        for j in range(s.ptr if frm is None else frm, len(s.tok)):
            w, t, p = s.tok[j]
            if p == part and w in c:
                if adv: s.ptr = j + 1
                return t
        s.miss += 1; return None
    def times(s, items, part=0, lead=0.3):
        p = s.parts[part]; ps, pe = p['start'], p['end']; n = len(items); out = []; last = s.st + 0.1
        for i, it in enumerate(items):
            t = s.find(it.get('k') or it.get('t'), part)
            t = ps + lead + max(0.0, pe - ps - lead - 0.8) * i / max(n, 1) if t is None else t - 0.12
            t = min(max(t, last + 0.12), s.en - 0.6); out.append(t); last = t
        return out
def item(it):
    if isinstance(it, dict): return it
    if isinstance(it, str): return {'t': it}
    d = {'t': it[0]}
    if len(it) > 1 and it[1]: d['c'] = it[1]
    if len(it) > 2 and it[2]: d['s'] = it[2]
    return d
def el(cls, style, inner, anim=None, at=0.0, d=0.5, extra=''):
    a = f' data-anim="{anim}" data-at="{at:.3f}" data-d="{d:.2f}"' if anim else ''
    return f'<div class="{cls}" style="{style}"{a}{extra}>{inner}</div>'
MK = {'*': '', '~': ' mk-coral', '^': ' mk-teal'}
def marked(text, S):
    out, pos = [], 0
    for m in re.finditer(r'([*~^])(.+?)\1', text):
        out.append(esc(text[pos:m.start()])); t = S.find(m.group(2), frm=0, adv=False)
        t = (t - 0.1) if t is not None else S.st + 0.8 + 0.5 * len(out)
        out.append(f'<span class="mark{MK[m.group(1)]}" data-anim="mark" data-at="{min(t, S.en - 0.6):.3f}" data-d="0.5">{esc(m.group(2))}</span>'); pos = m.end()
    return ''.join(out) + esc(text[pos:])
def icon(name, size, color, at, d=0.9, style=''):
    p = f'{V}/node_modules/lucide-static/icons/{name}.svg'
    if not os.path.exists(p): print('  missing icon', name); return ''
    s = re.sub(r'<!--.*?-->', '', open(p).read(), flags=re.S)
    s = re.sub(r'\s(width|height|class)="[^"]*"', '', s).replace('stroke-width="2"', 'stroke-width="1.6"')
    s = s.replace('<svg', f'<svg width="{size:.0f}" height="{size:.0f}" style="color:{col(color)}" data-anim="draw" data-at="{at:.3f}" data-d="{d}"', 1)
    return f'<div class="abs" style="{style}">{s}</div>'
def squiggle(w, color, at, d=0.6):
    w = int(w); return (f'<svg width="{w}" height="24" viewBox="0 0 {w} 24" data-anim="draw" data-at="{at:.3f}" data-d="{d}" style="display:block;margin:12px auto 0">'
            f'<path d="M4 13 C {w*.22:.0f} 4, {w*.45:.0f} 20, {w*.66:.0f} 11 S {w-30} 7, {w-4} 12" fill="none" stroke="{col(color)}" stroke-width="4" stroke-linecap="round"/></svg>')
# ---------------- templates ----------------
def T_title(S):
    sc = S.sc; t0 = S.st + 0.15; n = len(sc['title']); f = 86 if n <= 28 else 72 if n <= 44 else 60
    inner = el('t-num', '', esc(sc.get('n', '')), 'fade', t0) + el('t-title', f'font-size:{f}px', esc(sc['title']), 'fade', t0 + 0.3, 0.6)
    inner += squiggle(min(700, 40 + min(n, 30) * f * 0.36), 'coral', t0 + 0.9, 0.7)
    if sc.get('sub'): inner += el('t-sub', '', esc(sc['sub']), 'fade', t0 + 1.3)
    S.html.append(f'<div class="abs flexc" style="left:110px;right:110px;top:110px;bottom:90px;text-align:center">{inner}</div>')
def T_statement(S):
    sc = S.sc; t0 = S.st + 0.2; text = sc['text']; L = len(clean(text)); big, ic, by = sc.get('big'), sc.get('icon'), sc.get('by')
    left, right, align = 150, 150, 'center'
    if big:
        m = re.match(r'^(\D*?)(\d+(?:\.\d+)?)(.*)$', str(big)); tb = S.find(sc.get('bigk') or (m.group(2) if m else big), frm=0, adv=False)
        tb = (tb - 0.25) if tb is not None else t0 + 0.6
        if m:
            dec = len(m.group(2).split('.')[1]) if '.' in m.group(2) else 0
            nh = f'{esc(m.group(1))}<span data-anim="count" data-at="{tb:.3f}" data-d="1.1" data-to="{m.group(2)}" data-step="{10 ** -dec}">0</span>{esc(m.group(3))}'
        else: nh = esc(big)
        bf = 150 if len(str(big)) <= 5 else 110 if len(str(big)) <= 8 else 80
        bl = el('st-bigl', '', esc(sc['bigl']), 'fade', tb + 0.5) if sc.get('bigl') else ''
        S.html.append(f'<div class="abs flexc" style="left:50px;width:500px;top:110px;bottom:70px"><div class="st-big" style="font-size:{bf}px;color:{col(sc.get("bc"), "coral")}" data-anim="pop" data-at="{tb:.3f}" data-d="0.45">{nh}</div>{bl}</div>')
        left, right, align = 580, 90, 'left'
    elif ic:
        S.html.append(icon(ic, 220, sc.get('ic', 'coral'), t0, 1.3, 'left:110px;top:240px')); left, right, align = 410, 110, 'left'
    size = 44 if L <= 70 else 40 if L <= 120 else 35 if L <= 190 else 31 if L <= 270 else 28
    if big or ic: size = max(27, size - 4)
    if by: body = f'<div class="st-qm">“</div><div class="st-q" style="font-size:{size + 8}px">{marked(text, S)}</div>' + el('st-by', '', '— ' + esc(by), 'fade', t0 + 0.9)
    else: body = f'<div class="st-text" style="font-size:{size}px">{marked(text, S)}</div>'
    note = ''
    if sc.get('note'):
        tn = S.find(sc.get('notek') or sc['note'], frm=0, adv=False); tn = (tn - 0.1) if tn is not None else S.st + S.du * 0.6
        note = el('st-note', f'color:{col(sc.get("nc"), "teal")}', esc(sc['note']), 'fade', min(tn, S.en - 0.8))
    S.html.append(f'<div class="abs flexc" style="left:{left}px;right:{right}px;top:120px;bottom:70px;text-align:{align}" data-anim="fade" data-at="{t0:.3f}" data-d="0.5">{body}{note}</div>')
def T_chain(S):
    its = [item(i) for i in S.sc['items']]; n = len(its); ts = S.times(its)
    rows = [its] if n <= 5 else [its[:(n + 1) // 2], its[(n + 1) // 2:]]
    rh = 128 if len(rows) == 1 else 104; ys = [300] if len(rows) == 1 else [180, 425]
    bx, k = [], 0
    for r, row in enumerate(rows):
        m = len(row); gap = 66; w = min(250, (1170 - (m - 1) * gap) / m); x0 = 640 - (m * w + (m - 1) * gap) / 2
        for j, it in enumerate(row): bx.append((x0 + j * (w + gap), ys[r], w, rh, ts[k], it)); k += 1
    for i, (x, y, w, h, t, it) in enumerate(bx):
        c = it.get('c', 'ink')
        S.shapes.append({'s': 'rect', 'x': x, 'y': y, 'w': w, 'h': h, 'c': col(c), 't': t, 'd': 0.6, 'sd': S.si * 31 + i})
        S.html.append(el('box', f'left:{x:.0f}px;top:{y}px;width:{w:.0f}px;height:{h}px;font-size:{fs(len(it["t"]), [(14, 25), (30, 22), (55, 19), (999, 16)])}px;background:{tint(c)};border-radius:6px', esc(it['t']), 'fade', t + 0.2))
        if it.get('s'): S.html.append(el('bsub', f'left:{x - 12:.0f}px;top:{y + h + 10}px;width:{w + 24:.0f}px', esc(it['s']), 'fade', t + 0.45))
        if i:
            px, py, pw, ph = bx[i - 1][:4]
            pts = [[px + pw + 8, py + ph / 2], [x - 10, y + h / 2]] if abs(py - y) < 1 else [[px + pw / 2, py + ph + 8], [(px + pw / 2 + x + w / 2) / 2, (py + ph + y) / 2 + 12], [x + w / 2, y - 10]]
            S.shapes.append({'s': 'arrow', 'pts': pts, 'c': col('mute'), 't': t - 0.25, 'd': 0.35, 'sd': S.si * 17 + i})
def T_loop(S):
    its = [item(i) for i in S.sc['items']]; n = len(its); ts = S.times(its); cx, cy = 640, 402
    rx, ry = (440, 238) if n >= 6 else (360, 205); bw, bh = (180, 70) if n >= 7 else (210, 82)
    pos = [(cx + rx * math.cos(-math.pi / 2 + 2 * math.pi * i / n), cy + ry * math.sin(-math.pi / 2 + 2 * math.pi * i / n), -math.pi / 2 + 2 * math.pi * i / n) for i in range(n)]
    ac = col(S.sc.get('ac'), 'coral')
    for i, it in enumerate(its):
        x, y, _ = pos[i]; c = it.get('c', 'ink')
        S.shapes.append({'s': 'rect', 'x': x - bw / 2, 'y': y - bh / 2, 'w': bw, 'h': bh, 'c': col(c), 't': ts[i], 'd': 0.55, 'sd': S.si * 13 + i})
        S.html.append(el('box', f'left:{x - bw / 2:.0f}px;top:{y - bh / 2:.0f}px;width:{bw}px;height:{bh}px;font-size:{fs(len(it["t"]), [(16, 21), (32, 18), (60, 15), (999, 13)])}px;background:{tint(c)};border-radius:6px', esc(it['t']), 'fade', ts[i] + 0.2))
    for i in range(n):
        j = (i + 1) % n; a1 = pos[i][2]; a2 = pos[j][2] + (2 * math.pi if j == 0 else 0)
        pts = [[cx + rx * k * math.cos(a1 + (a2 - a1) * f), cy + ry * k * math.sin(a1 + (a2 - a1) * f)] for f, k in ((0.34, 1.0), (0.5, 1.05), (0.66, 1.0))]
        tt = ts[j] - 0.3 if j else min(ts[-1] + 0.5, S.en - 1.6)
        S.shapes.append({'s': 'arrow', 'pts': pts, 'c': ac, 't': tt, 'd': 0.4, 'sd': S.si * 19 + i, 'sw': 2.6})
    if S.sc.get('center'): S.html.append(el('ctr', f'left:{cx - 230}px;top:{cy - 48}px;width:460px', esc(S.sc['center']), 'fade', min(ts[-1] + 0.9, S.en - 0.7)))
def T_bars(S):
    sc = S.sc; its = sc['items']; n = len(its); vals = [float(i[1]) for i in its]; mx = float(sc.get('max') or max(vals) * 1.1 or 1); unit = sc.get('unit', '')
    rh = min(86, 460 / n); y0 = 150 + (460 - rh * n) / 2; ts = S.times([{'t': i[0], 'k': (i[4] if len(i) > 4 else None)} for i in its])
    for k, it in enumerate(its):
        y = y0 + k * rh; bh = rh * 0.58; c = col(it[2] if len(it) > 2 and it[2] else 'blue'); t = ts[k]; w = max(5, 640 * vals[k] / mx)
        S.html.append(el('bl', f'left:30px;top:{y:.0f}px;width:360px;height:{bh:.0f}px;font-size:{fs(len(it[0]), [(22, 24), (40, 20), (999, 17)])}px', esc(it[0]), 'fade', t))
        S.html.append(el('bar', f'left:410px;top:{y:.0f}px;width:{w:.0f}px;height:{bh:.0f}px;background:{c}', '', 'grow', t + 0.1, 0.9))
        if len(it) > 3 and it[3]: inner = esc(it[3])
        else:
            v = str(it[1]); dec = len(v.split('.')[1]) if '.' in v else 0
            inner = f'<span data-anim="count" data-at="{t + 0.1:.3f}" data-d="0.9" data-to="{v}" data-step="{10 ** -dec}">0</span>{esc(unit)}'
        S.html.append(el('bv', f'left:{410 + w + 14:.0f}px;top:{y:.0f}px;height:{bh:.0f}px;color:{c}', inner, 'fadein', t + 0.1, 0.3))
def T_dots(S):
    sc = S.sc; total = int(sc.get('total', 100)); hi, hi2 = int(sc.get('hi', 0)), int(sc.get('hi2', 0))
    cols = {100: 10, 200: 20, 50: 10, 1000: 40}.get(total, 10 if total <= 100 else 20); rows = -(-total // cols)
    sp = min(560 / cols, 440 / rows); dz = sp * 0.64; x0 = 60 + (560 - sp * cols) / 2; y0 = 150 + (460 - sp * rows) / 2
    order = sorted(range(total), key=lambda i: (i * 2654435761 + S.si * 97 + 12345) % 4294967296); h1, h2 = order[:hi], order[hi:hi + hi2]
    th = S.find(sc.get('k') or sc.get('label', ''), frm=0, adv=False); th = (th - 0.15) if th is not None else S.st + S.du * 0.3
    th2 = S.find(sc.get('k2'), frm=0, adv=False) if sc.get('k2') else None; th2 = (th2 - 0.15) if th2 is not None else th + 1.6
    g = ''.join(f'<div class="dot" style="left:{x0 + (i % cols) * sp:.1f}px;top:{y0 + (i // cols) * sp:.1f}px;width:{dz:.1f}px;height:{dz:.1f}px"></div>' for i in range(total))
    S.html.append(f'<div class="abs" style="left:0;top:0" data-anim="fadein" data-at="{S.st + 0.2:.3f}" data-d="0.6">{g}</div>')
    for grp, t, c in ((h1, th, sc.get('c', 'coral')), (h2, th2, sc.get('c2', 'amber'))):
        stg = min(0.06, 1.2 / max(len(grp), 1))
        for k, i in enumerate(grp):
            S.html.append(f'<div class="dot" style="left:{x0 + (i % cols) * sp:.1f}px;top:{y0 + (i // cols) * sp:.1f}px;width:{dz:.1f}px;height:{dz:.1f}px;background:{col(c)}" data-anim="pop" data-at="{min(t + k * stg, S.en - 0.5):.3f}" data-d="0.3"></div>')
    inner = el('dl', f'color:{col(sc.get("c"), "coral")}', esc(sc.get('label', '')), 'pop', th, 0.45) + (el('dt', '', esc(sc['text']), 'fade', th + 0.3) if sc.get('text') else '') + (el('ds', '', esc(sc['sub']), 'fade', min(th2 + 0.2, S.en - 0.6)) if sc.get('sub') else '')
    S.html.append(f'<div class="abs flexc" style="left:680px;width:540px;top:130px;bottom:80px">{inner}</div>')
def T_compare(S):
    L, R = S.sc['L'], S.sc['R']; lc, rc = col(L.get('c'), 'teal'), col(R.get('c'), 'coral'); li = [item(i) for i in L['items']]; ri = [item(i) for i in R['items']]
    ts = S.times([{'t': L['h']}] + li + [{'t': R['h']}] + ri); n = max(len(li), len(ri), 1); rh = min(96, 410 / n)
    for side, x, h, items, c, t0 in ((0, 60, L['h'], li, lc, 0), (1, 680, R['h'], ri, rc, 1 + len(li))):
        S.html.append(el('cmp-h', f'left:{x}px;width:540px;top:112px;color:{c};font-size:{46 if len(h) <= 24 else 36}px', esc(h), 'fade', ts[t0]))
        S.shapes.append({'s': 'line', 'x1': x + 110, 'y1': 178, 'x2': x + 430, 'y2': 178, 'c': c, 't': ts[t0] + 0.2, 'd': 0.4, 'sw': 3, 'sd': S.si + side})
        for k, it in enumerate(items):
            S.html.append(el('cmp-i', f'left:{x + 25}px;width:505px;top:{205 + k * rh:.0f}px;font-size:{fs(len(it["t"]), [(40, 25), (75, 22), (999, 19)])}px', esc(it['t']), 'fade', ts[t0 + 1 + k]))
    S.shapes.append({'s': 'line', 'x1': 640, 'y1': 125, 'x2': 640, 'y2': 655, 'c': col('mute'), 't': S.st + 0.2, 'd': 0.6, 'sw': 1.8, 'sd': S.si + 9})
def T_timeline(S):
    its = S.sc['items']; n = len(its); ts = S.times([{'t': tx} for _, tx in its]); y, xa, xb = 360, 80, 1200; seg = (xb - xa) / n
    S.shapes.append({'s': 'arrow', 'pts': [[xa - 20, y], [xb + 20, y]], 'c': col('ink'), 't': S.st + 0.2, 'd': 0.8, 'sw': 2.6, 'sd': S.si})
    for k, (d, tx) in enumerate(its):
        x = xa + seg * (k + 0.5); t = ts[k]
        S.shapes.append({'s': 'circle', 'x': x, 'y': y, 'dm': 22, 'c': col('coral'), 'f': col('coral'), 'fs': 'solid', 't': t, 'd': 0.3, 'sd': S.si * 5 + k})
        S.html.append(el('tl-d', f'left:{x - seg / 2:.0f}px;width:{seg:.0f}px;top:{y - 72}px', esc(d), 'pop', t, 0.4))
        S.html.append(el('tl-t', f'left:{x - seg / 2 + 8:.0f}px;width:{seg - 16:.0f}px;top:{y + 30}px;font-size:{fs(len(tx), [(40, 21), (80, 19), (130, 17), (999, 15)])}px', esc(tx), 'fade', t + 0.2))
def T_steps(S):
    its = S.sc['items']; n = len(its); two = n > 6; per = -(-n // 2) if two else n; rh = min(96, 470 / per); top = 135 + (470 - rh * per) / 2
    ts = S.times([{'t': it[1], 'k': (it[3] if len(it) > 3 else None)} for it in its])
    for k, it in enumerate(its):
        b, tx = str(it[0]), clean(it[1]); c = col(it[2] if len(it) > 2 and it[2] else 'coral'); cx = 0 if not two or k < per else 1; r = k if cx == 0 else k - per
        x = 90 if not two else 50 + cx * 610; y = top + r * rh; bd = min(60, rh * 0.78); tw = (1100 if not two else 560) - bd - 30
        S.shapes.append({'s': 'circle', 'x': x + bd / 2, 'y': y + rh / 2, 'dm': bd, 'c': c, 't': ts[k], 'd': 0.45, 'sd': S.si * 7 + k})
        if b.startswith('i:'): S.html.append(icon(b[2:], bd * 0.56, c, ts[k] + 0.1, 0.6, f'left:{x + bd * 0.22:.0f}px;top:{y + rh / 2 - bd * 0.28:.0f}px'))
        else: S.html.append(el('sp-b', f'left:{x:.0f}px;top:{y + rh / 2 - bd / 2:.0f}px;width:{bd:.0f}px;height:{bd:.0f}px;color:{c};font-size:{min(34, bd * 0.55):.0f}px', esc(b), 'pop', ts[k] + 0.1, 0.35))
        f = fs(len(tx), [(50, 26), (90, 23), (140, 20), (999, 18)]) if not two else fs(len(tx), [(40, 22), (80, 19), (999, 16)])
        S.html.append(el('sp-t', f'left:{x + bd + 22:.0f}px;top:{y:.0f}px;width:{tw:.0f}px;height:{rh:.0f}px;font-size:{f}px', esc(tx), 'fade', ts[k] + 0.15))
def T_quiz(S):
    sc = S.sc; p1, p2 = S.parts[1], S.parts[2]; t0 = S.st + 0.15; q = sc.get('q') or clean(sc['say']); a = sc.get('a') or clean(sc['sayA'])
    S.html.append(f'<div class="abs" style="left:110px;right:110px;top:92px" data-anim="fade" data-at="{t0:.3f}" data-d="0.5"><div class="qz-l">Pause and recall</div><div class="qz-q" style="font-size:{fs(len(q), [(70, 38), (120, 33), (999, 29)])}px">{esc(q)}</div></div>')
    rs, re_ = p1['start'], p1['end']; w = round(re_ - rs)
    S.html.append(f'<div class="abs" style="left:575px;top:400px;width:130px;height:130px" data-anim="fadein" data-at="{rs - 0.3:.3f}" data-d="0.3" data-out="{re_:.3f}">'
                  f'<svg width="130" height="130" data-anim="ring" data-at="{rs:.3f}" data-d="{re_ - rs:.2f}"><circle cx="65" cy="65" r="52" fill="none" stroke="#e3d9c6" stroke-width="10"/>'
                  f'<circle class="rg" cx="65" cy="65" r="52" fill="none" stroke="#D65A45" stroke-width="10" stroke-linecap="round" transform="rotate(-90 65 65)"/></svg>'
                  f'<div class="qz-n" style="left:0;top:38px;width:130px" data-anim="count" data-ease="none" data-at="{rs:.3f}" data-d="{re_ - rs:.2f}" data-from="{w}" data-to="0" data-step="1">{w}</div></div>')
    S.html.append(f'<div class="qz-a" style="left:160px;right:160px;top:385px" data-anim="fade" data-at="{p2["start"] - 0.1:.3f}" data-d="0.5"><div class="qz-ah">Answer</div><div class="qz-at" style="font-size:{fs(len(a), [(90, 28), (160, 25), (999, 22)])}px">{esc(a)}</div></div>')
TPL = dict(title=T_title, statement=T_statement, chain=T_chain, loop=T_loop, bars=T_bars, dots=T_dots, compare=T_compare, timeline=T_timeline, steps=T_steps, quiz=T_quiz)
out, miss = [], 0
for si, sc in enumerate(spec['scenes']):
    S = Sc(si, sc); TPL[sc['type']](S); pre = ''
    if sc.get('head'): pre += el('head', '', esc(sc['head']), 'fade', S.st + 0.1)
    if sc.get('ev'):
        e = sc['ev']; g = e[0] if len(e) > 2 and e[0] in 'ABCD' and e[1] in ' ·' else 'N'; pre += el(f'ev ev{g}', '', esc(e), 'fadein', S.st + 0.4, 0.4)
    svg = f'<svg class="rough" viewBox="0 0 1280 720" data-shapes="{esc(json.dumps(S.shapes))}"></svg>' if S.shapes else ''
    out.append(f'<div id="sc{si}" class="clip scene" data-start="{S.st:.3f}" data-duration="{S.du:.3f}" data-track-index="0">{svg}{pre}{"".join(S.html)}</div>'); miss += S.miss
tot = TM['total']
doc = (f'<!doctype html>\n<html><head><meta charset="utf-8"><title>{esc(spec.get("label", ch))}</title><link rel="stylesheet" href="theme.css"></head>\n<body>\n'
       f'<div id="root" data-composition-id="root" data-start="0" data-duration="{tot:.3f}" data-width="1280" data-height="720">\n'
       f'<audio id="vo" src="vo.wav" data-start="0" data-duration="{tot:.3f}" data-track-index="1"></audio>\n<div class="chlabel">{esc(spec.get("label", ""))}</div>\n'
       f'<div class="prog" data-anim="prog" data-at="0" data-d="{tot:.3f}"></div>\n' + '\n'.join(out) +
       '\n</div>\n<script src="gsap.min.js"></script><script src="rough.js"></script><script src="engine.js"></script>\n</body></html>\n')
open(f'{B}/index.html', 'w').write(doc)
NM = f'{V}/node_modules'; os.makedirs(f'{B}/fonts', exist_ok=True)
for s, d in [(f'{NM}/gsap/dist/gsap.min.js', 'gsap.min.js'), (f'{NM}/roughjs/bundled/rough.js', 'rough.js'), (f'{V}/engine/engine.js', 'engine.js'), (f'{V}/engine/theme.css', 'theme.css'),
             (f'{NM}/@fontsource/caveat/files/caveat-latin-400-normal.woff2', 'fonts/caveat-400.woff2'), (f'{NM}/@fontsource/caveat/files/caveat-latin-700-normal.woff2', 'fonts/caveat-700.woff2'),
             (f'{NM}/@fontsource/inter/files/inter-latin-400-normal.woff2', 'fonts/inter-400.woff2'), (f'{NM}/@fontsource/inter/files/inter-latin-600-normal.woff2', 'fonts/inter-600.woff2')]:
    shutil.copy(s, f'{B}/{d}')
print(f'BUILD {ch}: {len(out)} scenes, {tot / 60:.2f} min, whisper match {100 * good / max(len(stoks), 1):.0f}% of {len(stoks)} words, cue misses {miss}')
