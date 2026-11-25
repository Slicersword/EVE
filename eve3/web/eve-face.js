/* All display surfaces use the original expression artwork. */
(() => {
  'use strict';
  const art = window.EvaFaceArt;
  const names = new Set(art.names);
  let displayCount = 0;

  function mount(screen) {
    const scope = 'eve-display-' + ++displayCount;
    screen.classList.add('eve-face');
    screen.setAttribute('role', 'img');
    let expression, blinkTimer;
    let lookX = 0, lookY = 0;

    function show(name) {
      const next = names.has(name) ? name : 'idle';
      if (next === expression) return;
      expression = next;
      clearTimeout(blinkTimer);
      screen.classList.remove('is-blinking');
      screen.dataset.expression = next;
      screen.setAttribute('aria-label', 'EVE expression: ' + art.title(next));
      screen.innerHTML = art.svg(next, scope);
    }

    function look(x = 0, y = 0) {
      if (x === lookX && y === lookY) return;
      lookX = x;
      lookY = y;
      screen.style.setProperty('--look-x', x + '%');
      screen.style.setProperty('--look-y', y + '%');
    }

    function blink() {
      screen.classList.add('is-blinking');
      clearTimeout(blinkTimer);
      blinkTimer = setTimeout(() => screen.classList.remove('is-blinking'), 150);
    }

    show('idle');
    return {show, look, blink};
  }

  window.EveFace = Object.freeze({mount, title: art.title, names: art.names});
})();
