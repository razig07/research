#!/usr/bin/env python3
"""Cut the 1080p chapter renders into short lessons (quiz + teaser scenes removed) -> site/dist/{clips,posters} + site/lessons.json."""
import json, os, re, subprocess, sys
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SITE = f'{V}/site'; DIST = f'{SITE}/dist'
for d in ('clips', 'posters'): os.makedirs(f'{DIST}/{d}', exist_ok=True)
L = [('L00', 0, '0-3', 'How to use this course'),
 ('L01', 1, '0-4', 'The definition and its history'), ('L02', 1, '5-6', 'The proposed criteria'), ('L03', 1, '7-10', 'From the inside: plots and patterns'),
 ('L04', 1, '12-15', "How it's measured, and its status"), ('L05', 1, '16-20', 'Who has it'), ('L06', 1, '21-25', 'MD vs ordinary mind-wandering'),
 ('L07', 2, '0,2-6', 'Lens 1: a distinct disorder'), ('L08', 2, '7-9', 'Lenses 2 and 3: dissociation, addiction'), ('L09', 2, '10-15', 'Lenses 4 to 6, and how they fit'),
 ('L10', 3, '0,2-5', 'What starts an episode'), ('L11', 3, '6-8', 'What the fantasy pays out'), ('L12', 3, '9-11', 'The loop, link by link'), ('L13', 3, '12-15', 'Relief now, distress later'),
 ('L14', 4, '0,2-4', 'Time and focus'), ('L15', 4, '5-9', 'Work, mood, sleep, shame, social media'), ('L16', 4, '10-14', 'Success fantasies'), ('L17', 4, '15-17', 'Excitement and your pattern'),
 ('L18', 5, '0,2-6', 'Music vs verbal work'), ('L19', 5, '7-8', 'Your genres and creative work'), ('L20', 5, '9-12', 'Music as daydream fuel'),
 ('L21', 5, '13-14', 'Your playlist, part by part'), ('L22', 5, '15-16', 'Earworms and withdrawal'), ('L23', 5, '17-19', 'Silence, and what to use instead'),
 ('L24', 6, '0,2-4', 'Techniques ranked'), ('L25', 6, '5-7', 'Worked examples and producing'), ('L26', 6, '8-11', 'Illusions: tutorials and AI'), ('L27', 6, '12-14', 'Attention and learning'),
 ('L28', 7, '0,2-5', 'Deliberate practice and its limits'), ('L29', 7, '6-7', 'Feedback that works'), ('L30', 7, '8-9', 'Kind vs wicked: your skills'), ('L31', 7, '10-12', 'Patterns, experts, transfer'),
 ('L32', 8, '0,2-5', 'Ideation'), ('L33', 8, '6-9', 'Scripting and hooks'), ('L34', 8, '10-12', 'AI prompting'), ('L35', 8, '13-15', 'Editing, brand, business'), ('L36', 8, '16-18', 'Imagination in a container'),
 ('L37', 9, '0,2-3', 'Grades and the trial'), ('L38', 9, '4-7', '(a) When work gets uncomfortable'), ('L39', 9, '8-9', '(b) Music and (c) excitement'), ('L40', 9, '10-11', '(d) Success fantasies'),
 ('L41', 9, '12', '(e) Sleep and idle time'), ('L42', 9, '13-14', '(f) Daily and weekly system'), ('L43', 9, '15-17', '(g) Getting help, and the grades'),
 ('L44', 10, '0,8-11', 'The thread through everything')]
def rng(s):
    o = []
    for p in s.split(','): a, _, b = p.partition('-'); o += list(range(int(a), int(b or a) + 1))
    return o
def cl(t): return re.sub(r'[*~^]', '', str(t))
def it(i): return cl(i if isinstance(i, str) else i[0])
def note(sc):
    t = sc['type']
    if t == 'title': return None
    if t == 'statement':
        x = cl(sc['text'])
        if sc.get('by'): x = f'“{x}” ({sc["by"]})'
        if sc.get('big'): x = f'{sc["big"]} {sc.get("bigl", "")}: {x}'
        if sc.get('note'): x += f' {sc["note"]}.'
    elif t in ('chain', 'loop'): x = ' → '.join(it(i) for i in sc['items'])
    elif t == 'bars': x = '; '.join(f'{i[0]}: {i[3] if len(i) > 3 and i[3] else str(i[1]) + sc.get("unit", "")}' for i in sc['items'])
    elif t == 'dots': x = f'{sc.get("label", "")} {sc.get("text", "")}. {sc.get("sub", "")}'
    elif t == 'compare': x = f'{sc["L"]["h"]}: {", ".join(map(it, sc["L"]["items"]))}. {sc["R"]["h"]}: {", ".join(map(it, sc["R"]["items"]))}.'
    elif t == 'timeline': x = '; '.join(f'{d}: {tx}' for d, tx in sc['items'])
    elif t == 'steps': x = ' · '.join(((str(i[0]) + ' ') if not str(i[0]).startswith('i:') else '') + cl(i[1]) for i in sc['items'])
    else: x = ''
    return {'h': sc.get('head'), 'x': x.strip()}
only = set(sys.argv[1:]); out, quizzes, chapters, total = [], [], [], 0
for c in range(11):
    sp = json.load(open(f'{V}/script/ch{c:02d}.json')); chapters.append(sp['label'])
    for i, sc in enumerate(sp['scenes']):
        if sc['type'] == 'quiz': quizzes.append({'ch': c, 'i': i, 'q': sc.get('q') or cl(sc['say']), 'a': sc.get('a') or cl(sc['sayA']), 'full': cl(sc['sayA'])})
for lid, c, rs, title in L:
    ch = f'ch{c:02d}'; sp = json.load(open(f'{V}/script/{ch}.json'))['scenes']; tm = json.load(open(f'{V}/build/{ch}/timing.json'))['scenes']
    words = json.load(open(f'{V}/build/{ch}/vo.words.json'))['words']
    idx = [i for i in rng(rs) if sp[i]['type'] != 'quiz']; groups = []
    for i in idx:
        if groups and groups[-1][-1] == i - 1: groups[-1].append(i)
        else: groups.append([i])
    segs = [(tm[g[0]]['start'], tm[g[-1]]['start'] + tm[g[-1]]['dur']) for g in groups]; so, o = [], 0.0
    for a, b in segs: so.append(o); o += b - a
    scenes, cues = [], []
    for i in idx:
        st = tm[i]['start']; t = next(s0 + st - a for (a, b), s0 in zip(segs, so) if a - 1e-6 <= st < b)
        scenes.append({'i': i, 't': round(t, 2), 'n': note(sp[i])})
    for (a, b), s0 in zip(segs, so):
        line = []
        for w in [w for w in words if a <= w['start'] < b]:
            line.append(w)
            if len(line) >= 8 or w['word'].endswith(('.', '?', '!')): cues.append([round(line[0]['start'] - a + s0, 2), round(min(line[-1]['end'], b) - a + s0, 2), ' '.join(x['word'] for x in line)]); line = []
        if line: cues.append([round(line[0]['start'] - a + s0, 2), round(min(line[-1]['end'], b) - a + s0, 2), ' '.join(x['word'] for x in line)])
    clip = f'{DIST}/clips/{lid}.mp4'
    if not only or lid in only:
        cmd = ['ffmpeg', '-v', 'error', '-y']
        for a, b in segs: cmd += ['-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', f'{V}/out1080/{ch}.mp4']
        fc = ''.join(f'[{k}:v][{k}:a]' for k in range(len(segs))) + f'concat=n={len(segs)}:v=1:a=1[v][a]'
        subprocess.run(cmd + ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p',
                              '-c:a', 'aac', '-b:a', '80k', '-ac', '1', '-movflags', '+faststart', clip], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{o * 0.45:.2f}', '-i', clip, '-frames:v', '1', '-vf', 'scale=480:-1', '-q:v', '5', f'{DIST}/posters/{lid}.jpg'], check=True)
    real = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', clip]).decode()) if os.path.exists(clip) else 0.0
    sz = os.path.getsize(clip) / 1e6 if os.path.exists(clip) else 0.0; total += sz
    out.append({'id': lid, 'ch': c, 'title': title, 'dur': round(o, 1), 'scenes': scenes, 'cues': cues})
    print(f'{lid} expect={o:.1f}s real={real:.1f}s {sz:.1f}MB{"  MISMATCH" if abs(real - o) > 0.3 else ""}', flush=True)
json.dump({'chapters': chapters, 'lessons': out, 'quizzes': quizzes}, open(f'{SITE}/lessons.json', 'w'), ensure_ascii=False)
print(f'TOTAL {len(out)} lessons, {sum(x["dur"] for x in out) / 60:.1f} min, {total:.0f} MB, {len(quizzes)} original quizzes')
