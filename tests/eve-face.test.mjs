import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const web = new URL('../eve3/web/', import.meta.url);
const source = ['eva-face-art.js', 'eve-face.js'].map(name => readFileSync(new URL(name, web), 'utf8')).join('\n');
const catalog = JSON.parse(readFileSync(new URL('expressions.json', web), 'utf8'));

function fixture(reduced = false) {
  const queue = new Map();
  const motion = {matches: reduced, addEventListener() {}};
  const window = {
    Path2D: class { constructor(path) { this.path = path; } },
    matchMedia: () => motion,
    requestAnimationFrame(callback) {
      const id = ++frameId;
      queue.set(id, callback);
      return id;
    },
    cancelAnimationFrame(id) { queue.delete(id); },
  };
  let frameId = 0;
  const document = {
    addEventListener() {},
    createElement() {
      const draws = [];
      const gradient = () => ({stops: [], addColorStop(_, value) { this.stops.push(value); }});
      const context = new Proxy({
        createLinearGradient: gradient, createRadialGradient: gradient,
      }, {
        get(obj, name) {
          return obj[name] ?? ((...args) => draws.push([name, obj.fillStyle, ...args]));
        },
      });
      return {draws, setAttribute() {}, getContext: () => context};
    },
  };
  runInNewContext(source, {window, document});
  const renderer = window.EveFace;
  function mount(ambient = true) {
    const screen = {dataset: {}, classList: new Set(), setAttribute(name, value) { this[name] = value; },
      replaceChildren(canvas) { this.canvas = canvas; }};
    return {screen, display: renderer.mount(screen, {ambient})};
  }
  function frame(stamp) {
    const callbacks = [...queue.values()];
    queue.clear();
    for (const callback of callbacks) callback(stamp);
  }
  return {renderer, mount, frame, queue};
}

test('all 90 named expressions paint distinct poses on the shared Lumen canvas', () => {
  const {renderer, mount, frame, queue} = fixture(true);
  const {screen, display} = mount();
  assert.deepEqual(Array.from(renderer.names), catalog.expressions);
  assert.equal(screen.canvas.width, 1024);
  assert.equal(screen.canvas.height, 600);

  const poses = new Set();
  for (const [index, name] of catalog.expressions.entries()) {
    screen.canvas.draws.length = 0;
    display.show(name);
    frame(index * 16.7);
    assert.equal(screen.dataset.expression, name);
    assert.equal(screen['aria-label'], 'EVE expression: ' + renderer.title(name));
    assert.equal(screen.canvas.draws.filter(([op]) => op === 'drawImage').length, 2, name);
    const shape = screen.canvas.draws.filter(([op]) => ['translate', 'rotate', 'ellipse', 'stroke', 'moveTo', 'bezierCurveTo', 'quadraticCurveTo'].includes(op));
    poses.add(JSON.stringify(shape));
    assert.equal(queue.size, 0, 'reduced motion should draw only on demand');
  }
  assert.equal(poses.size, catalog.expressions.length);
  display.show('__proto__');
  assert.equal(screen.dataset.expression, 'idle');
});

test('gaze, blink and immediate red Alert use the same frame lifecycle', () => {
  const {mount, frame, queue} = fixture();
  const {screen, display} = mount(false);
  const paintedPupils = () => screen.canvas.draws.filter(([op, , x, y, rx]) => op === 'ellipse' && x === 0 && y === 0 && rx === 1).length;
  frame(0);
  assert.equal(paintedPupils(), 2);
  screen.canvas.draws.length = 0;
  display.look(6, 0);
  for (let i = 1; i < 45; i++) frame(i * 17);
  assert.ok(screen.canvas.draws.some(([op, , x, y]) => op === 'translate' && x > 20 && x < 30 && y === 0));
  display.blink();
  frame(765);
  for (let i = 46; i < 50; i++) frame(i * 17);
  screen.canvas.draws.length = 0;
  frame(850);
  assert.equal(paintedPupils(), 0);

  screen.canvas.draws.length = 0;
  display.show('alert');
  frame(867);
  const glass = screen.canvas.draws.find(([op, fill]) => op === 'fill' && fill?.stops)?.[1];
  assert.match(glass.stops[1], /^hsl\(6 /);
  assert.equal(paintedPupils(), 2);
  assert.equal(queue.size, 0);
});

test('the active face targets 60 draws per second on 60, 120 and 144 Hz displays', () => {
  for (const hz of [60, 120, 144]) {
    const {mount, frame} = fixture();
    const {screen} = mount();
    for (let i = 0; i < hz; i++) frame(i * 1000 / hz);
    const draws = screen.canvas.draws.filter(([op]) => op === 'fillRect').length;
    assert.equal(draws, 60, `at ${hz} Hz`);
  }
});
