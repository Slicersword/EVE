import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const web = new URL('../eve3/web/', import.meta.url);
const source = readFileSync(new URL('eve-face.js', web), 'utf8');
const catalog = JSON.parse(readFileSync(new URL('expressions.json', web), 'utf8'));

function fixture() {
  const window = {};
  const timers = [];
  runInNewContext(source, {
    window,
    clearTimeout: timer => { if (timer !== undefined) timers[timer] = undefined; },
    setTimeout: callback => timers.push(callback) - 1,
  });
  const part = () => {
    const style = new Map();
    const classList = new Set();
    style.setProperty = (key, value) => style.set(key, String(value));
    classList.remove = name => classList.delete(name);
    return { dataset: {}, style, classList };
  };
  const eyes = part(), mouth = part(), screen = part();
  eyes.children = [part(), part()];
  screen.querySelector = selector => selector === '.eve-face__eyes' ? eyes : mouth;
  screen.setAttribute = (name, value) => { screen[name] = value; };
  const renderer = window.EveFace;
  return { renderer, display: renderer.mount(screen), screen, eyes, mouth, timers };
}

test('every expression uses the same two eyes and mouth with a distinct pose', () => {
  const { renderer, display, screen, eyes, mouth } = fixture();
  assert.deepEqual(Array.from(renderer.names), catalog.expressions);
  const parts = Array.from(screen.innerHTML.matchAll(/<(\w+) class="([^"]+)"/g), match => match[2]);
  assert.deepEqual(parts, ['eve-face__eyes', 'eve-face__eye', 'eve-face__eye', 'eve-face__mouth']);
  const markup = screen.innerHTML;
  const signatures = new Set();
  for (const name of catalog.expressions) {
    display.show(name);
    assert.equal(screen.dataset.expression, name);
    assert.equal(screen.innerHTML, markup, name);
    assert.equal(screen['aria-label'], 'EVE expression: ' + renderer.title(name));
    signatures.add(JSON.stringify([
      screen.dataset.lids, [...screen.style], [...eyes.style],
      eyes.children.map(eye => [...eye.style]), mouth.dataset.shape, [...mouth.style],
    ]));
  }
  assert.equal(signatures.size, 90);
  display.show('not_an_expression');
  assert.equal(screen.dataset.expression, 'idle');
});

test('gaze and blink work on an extended expression without changing its face parts', () => {
  const { display, screen, eyes, timers } = fixture();
  display.show('mischievous');
  assert.equal(eyes.style.get('--look-x'), '4%');
  display.look(-6, 0);
  assert.equal(eyes.style.get('--look-x'), '-6%');
  display.look();
  assert.equal(eyes.style.get('--look-x'), '4%');
  display.blink();
  assert.ok(screen.classList.has('is-blinking'));
  timers.at(-1)();
  assert.equal(screen.classList.has('is-blinking'), false);
  assert.equal(screen.dataset.expression, 'mischievous');
});
