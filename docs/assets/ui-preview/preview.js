(() => {
  'use strict';
  const face = document.querySelector('#eve-display-preview');
  const expression = document.querySelector('#eve-preview-expression');
  const blink = document.querySelector('#eve-preview-blink');
  const play = document.querySelector('#eve-preview-play');
  const stop = document.querySelector('#eve-preview-stop');
  const status = document.querySelector('#eve-preview-status');
  const directions = document.querySelectorAll('[data-eve-preview-direction]');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const { expressions, samples } = window.EveKioskPreview;
  const { mount, title } = window.EveFace;
  const display = mount(face);
  let audio;

  for (const name of expressions) {
    expression.add(new Option(title(name), name));
  }
  expression.value = 'idle';

  function stopSound() {
    if (audio) {
      audio.pause();
      audio = undefined;
    }
    stop.disabled = true;
  }

  function render() {
    stopSound();
    const name = expression.value;
    display.show(name);
    display.look();
    blink.disabled = motion.matches || ['alert', 'dead'].includes(name);
    play.disabled = !Object.hasOwn(samples, name);
    status.textContent = play.disabled
      ? 'Sound samples are available for Happy, Love, and Surprised.'
      : 'Play the original ' + title(name) + ' cue.';
  }

  expression.addEventListener('change', render);
  motion.addEventListener('change', () => {
    blink.disabled = motion.matches || ['alert', 'dead'].includes(expression.value);
  });
  blink.addEventListener('click', () => display.blink());
  for (const button of directions) {
    button.addEventListener('click', () => display.look(Number(button.dataset.evePreviewDirection), 0));
  }
  play.addEventListener('click', async () => {
    const name = expression.value;
    if (!Object.hasOwn(samples, name)) return;
    stopSound();
    const clip = audio = new Audio(samples[name]);
    clip.volume = 0.175;
    stop.disabled = false;
    clip.addEventListener('ended', () => { if (audio === clip) stopSound(); }, {once: true});
    try {
      await clip.play();
    } catch {
      if (audio === clip) {
        stopSound();
        status.textContent = 'This browser could not play the sound sample.';
      }
    }
  });
  stop.addEventListener('click', stopSound);
  window.addEventListener('pagehide', stopSound);
  render();
  expression.disabled = false;
  for (const button of directions) button.disabled = false;
})();
