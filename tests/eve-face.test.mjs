import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const web = new URL('../eve3/web/', import.meta.url);
const source = ['eva-face-art.js', 'eve-face.js'].map(name => readFileSync(new URL(name, web), 'utf8')).join('\n');
const catalog = JSON.parse(readFileSync(new URL('expressions.json', web), 'utf8'));

function fixture() {
  const window = {}, timers = [];
  runInNewContext(source, {
    window, URLSearchParams, location: {search: ''},
    clearTimeout: timer => { if (timer !== undefined) timers[timer] = undefined; },
    setTimeout: callback => timers.push(callback) - 1,
  });
  function mount() {
    const style = new Map(), classList = new Set();
    classList.remove = name => classList.delete(name);
    style.setProperty = (name, value) => style.set(name, value);
    const screen = {dataset: {}, style, classList, setAttribute(name, value) { this[name] = value; }};
    return {screen, display: window.EveFace.mount(screen)};
  }
  return {renderer: window.EveFace, art: window.EvaFaceArt, mount, timers};
}

test('all 90 expressions use the original artwork on the shared display', () => {
  const {renderer, art, mount} = fixture();
  const {screen, display} = mount();
  assert.deepEqual(Array.from(renderer.names), catalog.expressions);
  for (const name of catalog.expressions) {
    display.show(name);
    assert.equal(screen.dataset.expression, name);
    assert.equal(screen.innerHTML, art.svg(name, 'eve-display-1'));
    assert.match(screen.innerHTML, /^<svg .*viewBox="0 0 380 255"/);
    assert.equal(screen.innerHTML.match(/class="eve-art-eye"/g).length, 2, name);
    assert.equal(screen['aria-label'], 'EVE expression: ' + renderer.title(name));
  }
  assert.match(art.svg('alert'), /#ff8f8f/);
  assert.notEqual(art.svg('idle').split('</defs>')[1], art.svg('happy').split('</defs>')[1]);
  display.show('unknown_expression');
  assert.equal(screen.dataset.expression, 'idle');
});

test('gaze, blinks and SVG paint references are isolated to each display', () => {
  const {mount, timers} = fixture();
  const {screen, display} = mount();
  const other = mount();
  display.show('mischievous');
  assert.match(screen.innerHTML, /id="eve-display-1-sh"/);
  assert.match(screen.innerHTML, /url\(#eve-display-1-sh\)/);
  assert.match(other.screen.innerHTML, /url\(#eve-display-2-eyeG\)/);
  display.look(-6, 0);
  assert.equal(screen.style.get('--look-x'), '-6%');
  display.look();
  assert.equal(screen.style.get('--look-x'), '0%');
  display.blink();
  assert.ok(screen.classList.has('is-blinking'));
  timers.at(-1)();
  assert.equal(screen.classList.has('is-blinking'), false);
  assert.equal(screen.dataset.expression, 'mischievous');
  assert.equal(other.screen.dataset.expression, 'idle');
});
