(function () {
  var tl = gsap.timeline({ paused: true });
  var NS = 'http://www.w3.org/2000/svg';
  function num(el, k, d) { var v = el && el.getAttribute(k); return v === null || v === undefined ? d : parseFloat(v); }
  function prepDraw(el, t, d) {
    var gs = el.querySelectorAll('path,line,polyline,polygon,circle,ellipse,rect');
    var n = gs.length, step = n > 1 ? Math.min(0.06, (d * 0.5) / n) : 0;
    for (var i = 0; i < n; i++) {
      var g = gs[i], len = 0;
      try { len = g.getTotalLength(); } catch (e) { len = 0; }
      if (!len || !isFinite(len)) len = 2;
      g.style.strokeDasharray = len + ' ' + len;
      tl.fromTo(g, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: Math.max(0.15, d - step * i), ease: 'power1.inOut' }, t + step * i);
    }
  }
  var shapeSvgs = document.querySelectorAll('svg.rough[data-shapes]');
  for (var q = 0; q < shapeSvgs.length; q++) {
    var svg = shapeSvgs[q], rc = rough.svg(svg), shapes = JSON.parse(svg.getAttribute('data-shapes'));
    shapes.forEach(function (s, i) {
      var o = { stroke: s.c || '#23262F', strokeWidth: s.sw || 2.2, roughness: s.r == null ? 1.15 : s.r, bowing: 1.1, seed: s.sd || (i * 7 + 3) };
      if (s.f) { o.fill = s.f; o.fillStyle = s.fs || 'hachure'; o.hachureGap = s.hg || 9; o.fillWeight = s.fw || 1.4; o.hachureAngle = -41; }
      var g = null;
      if (s.s === 'rect') g = rc.rectangle(s.x, s.y, s.w, s.h, o);
      else if (s.s === 'ellipse') g = rc.ellipse(s.x, s.y, s.w, s.h, o);
      else if (s.s === 'circle') g = rc.circle(s.x, s.y, s.dm, o);
      else if (s.s === 'line') g = rc.line(s.x1, s.y1, s.x2, s.y2, o);
      else if (s.s === 'curve' || s.s === 'arrow') {
        var pts = s.pts || [[s.x1, s.y1], [s.x2, s.y2]];
        g = document.createElementNS(NS, 'g');
        g.appendChild(pts.length > 2 ? rc.curve(pts, o) : rc.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], o));
        if (s.s === 'arrow') {
          var a = pts[pts.length - 2], b = pts[pts.length - 1], ang = Math.atan2(b[1] - a[1], b[0] - a[0]), L = s.hl || 15;
          [0.5, -0.5].forEach(function (da) { g.appendChild(rc.line(b[0], b[1], b[0] - L * Math.cos(ang + da), b[1] - L * Math.sin(ang + da), o)); });
        }
      }
      if (!g) return;
      svg.appendChild(g);
      var t = s.t || 0, d = s.d || 0.6;
      tl.fromTo(g, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t);
      prepDraw(g, t, d);
    });
  }
  var els = document.querySelectorAll('[data-anim]');
  for (var j = 0; j < els.length; j++) {
    var el = els[j], t = num(el, 'data-at', 0), d = num(el, 'data-d', 0.5), a = el.getAttribute('data-anim');
    if (a === 'fade') tl.fromTo(el, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: d, ease: 'power2.out' }, t);
    else if (a === 'fadein') tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: d }, t);
    else if (a === 'pop') tl.fromTo(el, { opacity: 0, scale: 0.3 }, { opacity: 1, scale: 1, duration: d, ease: 'back.out(2)' }, t);
    else if (a === 'grow') tl.fromTo(el, { scaleX: 0, transformOrigin: '0% 50%' }, { scaleX: 1, duration: d, ease: 'power2.out' }, t);
    else if (a === 'count') tl.fromTo(el, { innerText: num(el, 'data-from', 0) }, { innerText: num(el, 'data-to', 0), duration: d, ease: el.getAttribute('data-ease') || 'power1.out', snap: { innerText: num(el, 'data-step', 1) } }, t);
    else if (a === 'mark') tl.fromTo(el, { backgroundSize: '0% 42%' }, { backgroundSize: '100% 42%', duration: d, ease: 'power1.inOut' }, t);
    else if (a === 'draw') { tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t); prepDraw(el, t, d); }
    else if (a === 'ring') { var c = el.querySelector('circle.rg'), L = 2 * Math.PI * num(c, 'r', 40); c.style.strokeDasharray = L + ' ' + L; tl.fromTo(c, { strokeDashoffset: 0 }, { strokeDashoffset: L, duration: d, ease: 'none' }, t); }
    else if (a === 'prog') tl.fromTo(el, { scaleX: 0, transformOrigin: '0% 50%' }, { scaleX: 1, duration: d, ease: 'none' }, t);
    var out = el.getAttribute('data-out');
    if (out !== null) tl.to(el, { opacity: 0, duration: 0.3 }, parseFloat(out));
  }
  var sc = document.querySelectorAll('.scene');
  for (var k = 0; k < sc.length; k++) {
    var s0 = num(sc[k], 'data-start', 0), du = num(sc[k], 'data-duration', 1);
    tl.fromTo(sc[k], { opacity: 0 }, { opacity: 1, duration: 0.3 }, s0);
    tl.to(sc[k], { opacity: 0, duration: 0.25 }, s0 + du - 0.25);
  }
  var total = num(document.getElementById('root'), 'data-duration', tl.duration());
  tl.set({}, {}, total);
  window.__timelines = window.__timelines || {};
  window.__timelines['root'] = tl;
})();
