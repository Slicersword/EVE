(() => {
  'use strict';
  const frame = document.querySelector('#eve-display-preview');
  const expression = document.querySelector('#eve-preview-expression');
  const blink = document.querySelector('#eve-preview-blink');
  const play = document.querySelector('#eve-preview-play');
  const stop = document.querySelector('#eve-preview-stop');
  const status = document.querySelector('#eve-preview-status');
  const directions = document.querySelectorAll('[data-eve-preview-direction]');
  const { screen, expressions, samples } = window.EveKioskPreview;
  const { mount, title } = window.EveFace;
  let display;
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
    frame.title = 'EVE touchscreen showing ' + title(name);
    play.disabled = !Object.hasOwn(samples, name);
    status.textContent = play.disabled
      ? 'Sound samples are available for Happy, Love, and Surprised.'
      : 'Play the original ' + title(name) + ' cue.';
  }

  expression.addEventListener('change', render);
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
  frame.addEventListener('load', () => {
    const face = frame.contentDocument?.querySelector('#face');
    if (!face) return;
    display = mount(face);
    render();
    expression.disabled = blink.disabled = false;
    for (const button of directions) button.disabled = false;
  });
  frame.srcdoc = screen;
})();
