/* Shared Lumen renderer for the Pi touchscreen and the offline build guide. */
(() => {
  'use strict';
  const {profiles, names, title} = window.EvaFaceArt;
  const WIDTH = 1024, HEIGHT = 600, FRAME_MS = 1000 / 60;
  const EYES = [328, 696];
  const keys = Object.keys(profiles.idle).filter(key => typeof profiles.idle[key] === 'number');
  const clamp = (n, min, max) => Math.max(min, Math.min(n, max));
  const color = (h, s, l, a = 1) => `hsl(${h} ${s}% ${l}% / ${a})`;

  function palette(ctx, glow, hue) {
    const glass = ctx.createLinearGradient(0, -115, 0, 120);
    glass.addColorStop(0, color(hue - 6, 80, 85));
    glass.addColorStop(.19, color(hue, 69, 65));
    glass.addColorStop(.62, color(hue + 5, 58, 45));
    glass.addColorStop(1, color(hue + 15, 62, 25));

    const iris = ctx.createRadialGradient(-.13, -.17, .12, 0, 0, 1);
    iris.addColorStop(0, '#08161c');
    iris.addColorStop(.72, '#08161c');
    iris.addColorStop(.89, color(hue + 14, 54, 18));
    iris.addColorStop(1, color(hue, 61, 73, .68));

    // Cache the halo in a small sprite. Eye motion needs no per-frame blur.
    const g = glow.getContext('2d');
    const halo = g.createRadialGradient(80, 80, 8, 80, 80, 80);
    halo.addColorStop(0, color(hue, 74, 53, .24));
    halo.addColorStop(.56, color(hue, 67, 48, .095));
    halo.addColorStop(1, color(hue, 65, 43, 0));
    g.clearRect(0, 0, 160, 160);
    g.fillStyle = halo;
    g.fillRect(0, 0, 160, 160);

    return {
      glass, iris, light: color(hue, 73, 79), edge: color(hue, 80, 91, .46),
      reflection: color(hue - 10, 95, 91, .3), eyeMark: color(hue, 78, 76, .9),
    };
  }

  function eyeOutline(ctx, h) {
    const x = 127, y = h / 2, r = Math.min(61, h * .44);
    ctx.beginPath();
    ctx.moveTo(-x + r, -y);
    ctx.bezierCurveTo(-29, -y - 3, 29, -y - 3, x - r, -y);
    ctx.quadraticCurveTo(x, -y, x, -y + r);
    ctx.lineTo(x, y - r);
    ctx.quadraticCurveTo(x, y, x - r, y);
    ctx.bezierCurveTo(25, y + 2, -25, y + 2, -x + r, y);
    ctx.quadraticCurveTo(-x, y, -x, y - r);
    ctx.lineTo(-x, -y + r);
    ctx.quadraticCurveTo(-x, -y, -x + r, -y);
    ctx.closePath();
  }

  const marks = {
    heart: new window.Path2D('M0 .42C-.16 .28 -.53 .02 -.53 -.22C-.53 -.52 -.16 -.6 0 -.32C.16 -.6 .53 -.52 .53 -.22C.53 .02 .16 .28 0 .42Z'),
    star: new window.Path2D('M0 -.66Q.14 -.14 .61 0Q.14 .14 0 .66Q-.14 .14 -.61 0Q-.14 -.14 0 -.66Z'),
    spiral: new window.Path2D('M.56 0A.56 .56 0 1 1 -.56 0A.39 .39 0 1 1 .22 0A.22 .22 0 1 1 -.22 0'),
    cross: new window.Path2D('M-.35 -.35L.35 .35M.35 -.35L-.35 .35'),
    scan: new window.Path2D('M-.52 -.27H.15M-.27 0H.52M-.45 .27H.25'),
    listen: new window.Path2D('M.38 -.78Q1.1 0 .38 .78M-.24 -.48Q.16 0 -.24 .48'),
  };

  function ellipse(ctx, x, y, rx, ry, fill, rotation = 0) {
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, rotation, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
  }

  function drawEye(ctx, x, y, height, tilt, gaze, p, detail, paint, side) {
    const h = Math.max(0, height);
    const openness = clamp((h - 20) / 19, 0, 1);
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(tilt);
    if (openness < 1) {
      ctx.globalAlpha = 1 - openness;
      ctx.strokeStyle = paint.light;
      ctx.lineWidth = 5;
      ctx.beginPath();
      ctx.moveTo(-98, 0);
      ctx.quadraticCurveTo(0, 11 - Math.max(0, p.smile) * 50, 98, 0);
      ctx.stroke();
    }
    if (openness > 0) {
      ctx.globalAlpha = openness;
      eyeOutline(ctx, h);
      ctx.fillStyle = paint.glass;
      ctx.fill();
      ctx.lineWidth = 1.7;
      ctx.strokeStyle = paint.edge;
      ctx.stroke();
      ctx.save();
      ctx.clip();
      const r = 157 * p.pupil;
      ctx.save();
      ctx.translate(gaze.x, gaze.y);
      ctx.scale(r, r * 1.13);
      ellipse(ctx, 0, 0, 1, 1, paint.iris);
      if (detail) {
        ctx.fillStyle = ctx.strokeStyle = paint.eyeMark;
        ctx.lineWidth = .08;
        if (detail === 'heart' || detail === 'star') ctx.fill(marks[detail]);
        else ctx.stroke(marks[detail]);
      }
      ellipse(ctx, -.34, -.59, .25, .108, '#eafff4', -.38);
      ellipse(ctx, .34, .48, .047, .047, '#cffaeaab');
      ellipse(ctx, .45, -.55, .028, .028, '#eafff46a');
      ctx.restore();
      ctx.strokeStyle = paint.reflection;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(-74, h * .4);
      ctx.quadraticCurveTo(0, h * .49, 69, h * .4);
      ctx.stroke();
      ctx.restore();

      if (h > 125) {
        ctx.globalAlpha *= clamp((h - 125) / 24, 0, 1);
        ctx.strokeStyle = '#f8d697bc';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(side * 108, h / 2 - 29);
        ctx.lineTo(side * 108, h / 2 - 19);
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  function drawFace(ctx, glow, p, target, paint, gaze, blink, time, moving) {
    ctx.fillStyle = '#060d10';
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    const breath = moving ? Math.sin(time * Math.PI * 2 / 5.2) * 1.9 : 0;
    ctx.lineCap = ctx.lineJoin = 'round';
    ctx.strokeStyle = paint.light;
    for (const [index, x] of EYES.entries()) {
      const side = index === 0 ? -1 : 1;
      const aperture = index === 0 ? p.left : p.right;
      const tilt = index === 0 ? p.tiltL : p.tiltR;
      ctx.globalAlpha = .3 + .65 * Math.min(aperture, 1);
      ctx.drawImage(glow, x - 170, 256 - 177 + breath, 340, 354);
      ctx.globalAlpha = 1;
      if (Math.abs(p.brow) + Math.abs(p.furrow) > .03) {
        const arch = 115 - p.brow * 24 - Math.max(0, aperture - 1) * 41;
        const angle = p.furrow * side * 13;
        ctx.globalAlpha = .53 * clamp((Math.abs(p.brow) + Math.abs(p.furrow)) * 2.5, 0, 1);
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.moveTo(x - 60, arch + angle);
        ctx.quadraticCurveTo(x, arch - 14 - p.brow * 8, x + 60, arch - angle);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
      drawEye(ctx, x, 256 + breath, 210 * aperture * blink, tilt, gaze, p, target.mark, paint, side);
      if (p.blush > .01) {
        ctx.globalAlpha = .54 * p.blush;
        ctx.strokeStyle = '#f1b5a6';
        ctx.lineWidth = 3;
        ctx.beginPath();
        for (let i = -1; i <= 1; i++) {
          ctx.moveTo(x + side * 93 + i * 10, 377);
          ctx.lineTo(x + side * 93 + i * 10 - 4, 388);
        }
        ctx.stroke();
        ctx.globalAlpha = 1;
        ctx.strokeStyle = paint.light;
      }
    }
    if (p.tear > .01) {
      ctx.globalAlpha = .78 * p.tear;
      ctx.fillStyle = '#9adff9';
      ctx.beginPath();
      ctx.moveTo(771, 347);
      ctx.quadraticCurveTo(753, 370, 770, 375);
      ctx.quadraticCurveTo(789, 375, 771, 347);
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    const jaw = p.jaw + (moving && target === profiles.speaking ? .32 * (.5 + .5 * Math.sin(time * 13)) : 0);
    const smile = Math.max(0, p.smile);
    const width = 58 + 8 * smile - jaw * (30 - 16 * smile);
    const curve = 45 * p.smile;
    ctx.lineWidth = 7;
    ctx.beginPath();
    ctx.moveTo(512 - width, 424);
    ctx.bezierCurveTo(512 - width, 424 + curve - 28 * jaw, 512 + width, 424 + curve - 28 * jaw, 512 + width, 424);
    if (jaw > .045) {
      ctx.bezierCurveTo(512 + width, 424 + curve + 42 * jaw, 512 - width, 424 + curve + 42 * jaw, 512 - width, 424);
      ctx.fillStyle = '#09171c';
      ctx.fill();
    }
    ctx.stroke();
    if (target.accent === 'dots') {
      for (let i = 0; i < 3; i++) {
        ctx.globalAlpha = moving ? .48 + .34 * Math.sin(time * 4 - i) : .68;
        ellipse(ctx, 496 + 16 * i, 474, 3.2, 3.2, paint.light);
      }
    } else if (target.accent === 'sparkles') {
      ctx.fillStyle = paint.light;
      for (const side of [-1, 1]) {
        ctx.save();
        ctx.translate(512 + side * 341, 211);
        ctx.scale(16, 16);
        ctx.globalAlpha = .77;
        ctx.fill(marks.star);
        ctx.scale(.48, .48);
        ctx.translate(side * 2.5, -4);
        ctx.globalAlpha = .54;
        ctx.fill(marks.star);
        ctx.restore();
      }
    } else if (target.accent === 'listen') {
      ctx.globalAlpha = .5;
      for (const side of [-1, 1]) {
        ctx.save();
        ctx.translate(512 + side * 334, 256);
        ctx.scale(side * 21, 21);
        ctx.lineWidth = .13;
        ctx.stroke(marks.listen);
        ctx.restore();
      }
    }
    ctx.globalAlpha = 1;
  }

  function blinkEnvelope(seconds) {
    if (seconds < 0 || seconds >= .25) return 1;
    if (seconds < .085) return 1 - .975 * Math.sin(seconds / .085 * Math.PI / 2);
    if (seconds < .105) return .025;
    return 1 - .975 * (1 - (seconds - .105) / .145) ** 3;
  }

  function mount(screen, {ambient = true} = {}) {
    const canvas = document.createElement('canvas');
    canvas.width = WIDTH;
    canvas.height = HEIGHT;
    canvas.setAttribute('aria-hidden', 'true');
    const ctx = canvas.getContext('2d', {alpha: false});
    const glow = document.createElement('canvas');
    glow.width = glow.height = 160;
    const view = window;
    const preference = view.matchMedia('(prefers-reduced-motion: reduce)');
    const gaze = {x: 0, y: 0};
    const current = {...profiles.idle};
    let target = profiles.idle, expression, paletteHue, paint;
    let lookX = 0, lookY = 0, directed = false;
    let time = 0, prev = null, deadline = null, frame = null;
    let blinkStart = -1, nextBlink = 3.6;

    screen.classList.add('eve-face');
    screen.setAttribute('role', 'img');
    screen.replaceChildren(canvas);

    function requestDraw() {
      if (frame === null && !document.hidden) {
        frame = view.requestAnimationFrame(draw);
      }
    }

    function draw(stamp) {
      frame = null;
      const moving = !preference.matches;
      if (moving && deadline !== null && stamp + 1.25 < deadline) {
        requestDraw();
        return;
      }
      const dt = prev === null ? FRAME_MS / 1000 : clamp((stamp - prev) / 1000, 0, .1);
      prev = stamp;
      // Keep the target cadence on displays that refresh faster than 60 Hz.
      deadline = deadline === null ? stamp + FRAME_MS
        : deadline + Math.max(1, Math.floor((stamp - deadline) / FRAME_MS) + 1) * FRAME_MS;
      if (moving) time += dt;
      const amount = moving ? 1 - Math.exp(-dt * 11) : 1;
      let changing = false;
      for (const key of keys) {
        const diff = key === 'hue'
          ? (target.hue - current.hue + 540) % 360 - 180
          : target[key] - current[key];
        if (Math.abs(diff) > .003) {
          current[key] += diff * amount;
          changing = true;
        } else current[key] = target[key];
      }
      current.hue = (current.hue + 360) % 360;

      const ambientGaze = moving && ambient && !directed && expression === 'idle';
      const x = clamp(current.x * 61 + lookX + (ambientGaze ? Math.sin(time * 1.32) * 5.5 : 0), -34, 34);
      const y = clamp(current.y * 45 + lookY + (ambientGaze ? Math.sin(time * .8) * 2 : 0), -24, 24);
      gaze.x = Math.abs(x - gaze.x) < .08 ? x : gaze.x + (x - gaze.x) * amount;
      gaze.y = Math.abs(y - gaze.y) < .08 ? y : gaze.y + (y - gaze.y) * amount;

      const autoBlink = ambient && !['alert', 'dead'].includes(expression);
      if (moving && autoBlink && time >= nextBlink) {
        blinkStart = time;
        nextBlink = time + 3.8 + Math.random() * 1.8;
      }
      const blinking = moving && time - blinkStart < .25;
      const hue = Math.round(current.hue / 3) * 3 % 360;
      if (hue !== paletteHue) {
        paletteHue = hue;
        paint = palette(ctx, glow, hue);
      }
      const animateDetails = moving && (autoBlink || expression === 'speaking');
      drawFace(ctx, glow, current, target, paint, gaze, blinking ? blinkEnvelope(time - blinkStart) : 1, time, animateDetails);
      if (moving && (autoBlink || changing || gaze.x !== x || gaze.y !== y || blinking || expression === 'speaking')) {
        requestDraw();
      } else prev = deadline = null;
    }

    function show(name) {
      const next = Object.hasOwn(profiles, name) ? name : 'idle';
      if (next === expression) return;
      expression = next;
      target = profiles[next];
      if (next === 'alert') {
        Object.assign(current, target);
        blinkStart = -1;
      }
      screen.dataset.expression = next;
      screen.setAttribute('aria-label', 'EVE expression: ' + title(next));
      requestDraw();
    }

    function look(x = 0, y = 0) {
      const nextX = Number.isFinite(x) ? clamp(x, -10, 10) * 4.4 : 0;
      const nextY = Number.isFinite(y) ? clamp(y, -10, 10) * 3.6 : 0;
      if (lookX === nextX && lookY === nextY) return;
      lookX = nextX;
      lookY = nextY;
      directed = Boolean(lookX || lookY);
      requestDraw();
    }

    function blink() {
      if (preference.matches || expression === 'alert' || expression === 'dead') return;
      blinkStart = time;
      requestDraw();
    }

    function visibility() {
      if (frame !== null) view.cancelAnimationFrame(frame);
      frame = prev = deadline = null;
      requestDraw();
    }

    document.addEventListener('visibilitychange', visibility);
    preference.addEventListener('change', visibility);
    show('idle');

    return {show, look, blink};
  }

  window.EveFace = Object.freeze({mount, title, names});
})();
