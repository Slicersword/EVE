(() => {
  'use strict';
  const frame = document.querySelector('#eve-display-preview');
  const expression = document.querySelector('#eve-preview-expression');
  const blink = document.querySelector('#eve-preview-blink');
  const play = document.querySelector('#eve-preview-play');
  const stop = document.querySelector('#eve-preview-stop');
  const status = document.querySelector('#eve-preview-status');
  const directions = document.querySelectorAll('[data-eve-preview-direction]');
  const { screen, expressions, core, samples } = window.EveKioskPreview;
  const art = window.EvaFaceArt;
  const coreNames = new Set(core);
  let blinkTimer;
  let audio;

  for (const name of expressions) {
    expression.add(new Option(art.title(name), name));
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
    const doc = frame.contentDocument;
    const face = doc?.querySelector('#face');
    const extended = doc?.querySelector('#extended');
    if (!face || !extended) return;
    clearTimeout(blinkTimer);
    stopSound();
    const name = expression.value;
    const isCore = coreNames.has(name);
    face.hidden = !isCore;
    face.className = isCore ? name : 'idle';
    extended.hidden = isCore;
    extended.innerHTML = isCore ? '' : art.svg(name);
    doc.querySelector('#eyes').style.transform = '';
    frame.title = 'EVE touchscreen showing ' + art.title(name);
    expression.disabled = false;
    blink.disabled = !isCore || name === 'sleepy';
    for (const button of directions) button.disabled = !isCore;
    play.disabled = !Object.hasOwn(samples, name);
    status.textContent = play.disabled
      ? 'Sound samples are available for Happy, Love, and Surprised.'
      : 'Play the original ' + art.title(name) + ' cue.';
  }

  expression.addEventListener('change', render);
  blink.addEventListener('click', () => {
    const face = frame.contentDocument.querySelector('#face');
    face.classList.add('blink');
    clearTimeout(blinkTimer);
    blinkTimer = setTimeout(() => face.classList.remove('blink'), 160);
  });
  for (const button of directions) {
    button.addEventListener('click', () => {
      frame.contentDocument.querySelector('#eyes').style.transform =
        'translateX(' + button.dataset.evePreviewDirection + 'vw)';
    });
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
  frame.addEventListener('load', render);
  frame.srcdoc = screen;
})();
