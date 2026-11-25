/* Local kiosk cues. The face stays quiet until the owner taps Enable sounds. */
(() => {
  'use strict';
  let pack, mode, enabled = false, active, blockedUntil = Infinity;
  let lastExpression, permitted = false;
  const quietTail = 550;

  function stop() {
    if (active) {
      active.pause();
      active.currentTime = 0;
      active = undefined;
    }
  }

  function play(name, volume) {
    if (!pack || !Object.hasOwn(pack.clips, name)) return;
    stop();
    const sound = new Audio('/sfx/' + name + '.wav');
    sound.volume = volume;
    active = sound;
    sound.play().catch(() => { if (active === sound) active = undefined; });
  }

  window.EveExpressionAudio = {
    async load() {
      if (!pack) {
        const response = await fetch('/expression-assets.json');
        if (!response.ok) throw new Error('Expression pack unavailable');
        pack = await response.json();
        mode = pack.default_mode;
      }
      return pack;
    },
    configure(on, selected) {
      enabled = on;
      if (pack && Object.hasOwn(pack.modes, selected)) mode = selected;
      stop();
    },
    update(status) {
      const name = status?.expression;
      const changed = name !== lastExpression;
      lastExpression = name;
      const nextAllowed = status?.expression_cues_allowed === true;
      if (!nextAllowed) {
        permitted = false;
        blockedUntil = Infinity;
        stop();
        return;
      }
      if (!permitted) blockedUntil = performance.now() + quietTail;
      permitted = true;
      if (enabled && changed && performance.now() >= blockedUntil &&
          pack?.modes[mode]?.includes(name)) play(name, 0.175);
    },
    preview(name) { play(name, 0.175); },
    stop,
  };
})();
