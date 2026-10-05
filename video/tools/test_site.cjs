// Headless check of the learning site over file:// : console errors, video load, one quiz round, progress saved, screenshots.
const path = require('path'); let pptr; try { pptr = require('puppeteer-core') } catch (e) { pptr = require(require('child_process').execSync('find ' + __dirname + '/../node_modules -maxdepth 4 -type d -name puppeteer-core | head -1').toString().trim()) }
(async () => {
  const dir = process.argv[2] || path.resolve(__dirname, '../site/dist'), url = 'file://' + dir + '/index.html';
  const b = await pptr.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'], headless: true });
  const p = await b.newPage(); await p.setViewport({ width: 1280, height: 900 }); const errs = [];
  p.on('pageerror', e => errs.push('pageerror: ' + e.message)); p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()) });
  await p.goto(url + '#/home'); await new Promise(r => setTimeout(r, 800));
  await p.goto(url + '#/lesson/L12'); await new Promise(r => setTimeout(r, 1500));
  const rs = await p.evaluate(() => { const v = document.querySelector('#v'); return { rs: v.readyState, dur: v.duration, err: v.error && v.error.code } });
  await p.evaluate(() => { const v = document.querySelector('#v'); v.muted = true; v.currentTime = 20; return v.play().catch(() => 0) }); await new Promise(r => setTimeout(r, 2500));
  const cc = await p.evaluate(() => document.querySelector('#cc').textContent);
  await p.click('#qgo');
  for (let k = 0; k < 3; k++) {
    await p.evaluate(() => {
      const q = s => document.querySelector(s); if (q('#ti')) { q('#ti').value = 'test'; q('#tgo').click() } else if (q('#ngo')) q('#ngo').click(); else if (q('#rgo')) { q('#ra').value = 'test'; q('#rgo').click() }
      else { let o; while ((o = [...document.querySelectorAll('.opt')].find(x => !x.classList.contains('hide') && !x.disabled)) && !q('[data-c]')) o.click() }
    });
    await p.evaluate(() => document.querySelector('[data-c="1"]').click());
    await p.evaluate(() => { const d = document.querySelector('#kdone'); if (d) { const c = document.querySelector('.kp input'); if (c) c.click(); d.click() } });
    if (k === 0) await p.screenshot({ path: path.resolve(__dirname, '../qa/site_quiz.png') });
    await p.evaluate(() => document.querySelector('#nx').click()); await new Promise(r => setTimeout(r, 200));
  }
  const st = await p.evaluate(() => { const s = JSON.parse(localStorage.getItem('mdlearn.v1') || '{}'); return { q: Object.keys(s.q || {}).length, lesW: (s.les || {}).L12 } });
  await p.goto(url + '#/stats'); await new Promise(r => setTimeout(r, 600)); await p.screenshot({ path: path.resolve(__dirname, '../qa/site_stats.png') });
  await p.goto(url + '#/home'); await new Promise(r => setTimeout(r, 600)); await p.screenshot({ path: path.resolve(__dirname, '../qa/site_home.png') });
  console.log(JSON.stringify({ video: rs, caption: cc.slice(0, 60), saved: st, errors: errs.slice(0, 8) }));
  await b.close();
})().catch(e => { console.error('TEST FAILED', e.message); process.exit(1) });
