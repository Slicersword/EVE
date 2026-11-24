import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const p = require('../site/assets/progress-state.js');
const manifest = JSON.parse(fs.readFileSync(new URL('../_data/build_progress.json', import.meta.url)));
function memory(initial) {
  const values = new Map(initial ? [[p.KEY, initial]] : []);
  return {getItem: key => values.has(key) ? values.get(key) : null,
    setItem: (key, value) => values.set(key, value), values};
}
test('manifest covers every stage, has stable unique IDs and only internal instruction links', () => {
  const tasks = manifest.groups.flatMap(g => g.tasks);
  assert.equal(new Set(tasks.map(t => t.id)).size, tasks.length);
  assert.ok(tasks.length >= 40);
  for (let n = 0; n <= 17; n++) assert.ok(tasks.find(t => t.id === 'm' + String(n).padStart(2, '0')));
  for (const task of tasks) {
    assert.match(task.id, /^[a-z][a-z0-9-]+$/);
    assert.match(task.href, /^docs\/[A-Z_]+\.html(?:#[a-z0-9-]+)?$/);
    assert.ok(task.title && task.detail);
  }
});
test('new notebooks start paused with zero completed tasks and no storage writes', () => {
  const storage = memory(), book = p.notebook(storage, manifest);
  assert.equal(book.state.enabled, false);
  assert.equal(p.summary(book.state, manifest).done, 0);
  assert.equal(storage.values.size, 0);
});
test('checkmarks, Unicode notes and dates persist through reload and export/import', () => {
  const storage = memory(), book = p.notebook(storage, manifest);
  book.enable(true); book.update('parts', {done: true, note: 'मोजले: 5.01 V <script>not executed</script>'});
  const date = book.state.tasks.parts.completedAt;
  book.update('parts', {note: 'वायरिंग checked'});
  assert.equal(book.state.tasks.parts.completedAt, date);
  assert.deepEqual(p.notebook(storage, manifest).state, book.state);
  const other = p.notebook(memory(), manifest); other.import(book.export());
  assert.deepEqual(other.state, book.state);
  assert.equal(p.summary(other.state, manifest).done, 1);
});
test('unchecking clears its completion date; pause keeps notes; reset clears notebook', () => {
  const book = p.notebook(memory(), manifest); book.enable(true);
  book.update('parts', {done: true, note: 'retain me'}); book.enable(false);
  assert.equal(book.state.tasks.parts.note, 'retain me');
  book.update('parts', {done: false});
  assert.equal(book.state.tasks.parts.completedAt, null);
  book.reset(); assert.deepEqual(book.state, p.empty());
});
test('invalid imports never replace the current notebook or stored data', () => {
  const storage = memory(), book = p.notebook(storage, manifest); book.enable(true);
  book.update('parts', {done: true}); const before = book.export();
  const bad = ['{', 'null', '{}', JSON.stringify({...p.empty(), schemaVersion: 2}),
    JSON.stringify({...p.empty(), tasks: {parts: {done: 'yes', note: '', completedAt: null}}}),
    JSON.stringify({...p.empty(), tasks: {parts: {done: true, note: '', completedAt: 'bad'}}}),
    JSON.stringify({...p.empty(), tasks: {parts: {done: false, note: 'x'.repeat(2001), completedAt: null}}}),
    JSON.stringify({...p.empty(), tasks: {unknown: {done: true, note: '', completedAt: null}}}),
    '{"schemaVersion":1,"project":"EVE","enabled":true,"tasks":{"__proto__":{"done":true,"note":"","completedAt":null}}}',
    'x'.repeat(p.MAX_BYTES + 1)];
  for (const text of bad) {
    assert.throws(() => book.import(text));
    assert.deepEqual(p.parse(book.export(), manifest), p.parse(before, manifest));
    assert.deepEqual(p.parse(storage.values.get(p.KEY), manifest), book.state);
  }
  assert.equal({}.done, undefined);
});
test('storage failure leaves an exportable session and an explicit warning', () => {
  const book = p.notebook({getItem: () => null, setItem() {throw new Error('quota');}}, manifest);
  book.enable(true); book.update('parts', {done: true});
  assert.equal(book.persistent, false); assert.match(book.warning, /Export/);
  assert.equal(p.parse(book.export(), manifest).tasks.parts.done, true);
  const unavailable = p.notebook(null, manifest); unavailable.enable(true);
  assert.equal(unavailable.persistent, false);
});
test('unreadable stored backup is preserved until explicit reset/import', () => {
  const storage = memory('broken backup'), book = p.notebook(storage, manifest);
  assert.match(book.warning, /could not be read/);
  book.enable(true); assert.equal(storage.values.get(p.KEY), 'broken backup');
  book.reset(); assert.deepEqual(p.parse(storage.values.get(p.KEY), manifest), p.empty());
});
test('validated records do not retain unknown fields from imported JSON', () => {
  const value = {...p.empty(), config: {drive_enabled: true}, token: 'not retained'};
  const parsed = p.parse(JSON.stringify(value), manifest);
  assert.deepEqual(parsed, p.empty());
});
