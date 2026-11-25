import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const script = readFileSync(new URL('../eve3/web/expression-audio.js', import.meta.url), 'utf8');
const assets = JSON.parse(readFileSync(new URL('../eve3/web/expressions.json', import.meta.url), 'utf8'));

test('plays the current expression once after the quiet interval and cancels it when blocked', async () => {
  const played = [], paused = [], window = {};
  let now = 0;
  class Audio {
    constructor(url) { this.url = url; }
    play() { played.push(this.url); return Promise.resolve(); }
    pause() { paused.push(this.url); }
  }
  runInNewContext(script, {
    window, Audio, performance: { now: () => now },
    fetch: async () => ({ ok: true, json: async () => assets }),
  });
  const audio = window.EveExpressionAudio;
  await audio.load();
  const mode = Object.keys(assets.modes).find(key => assets.modes[key].includes('happy'));
  assert.ok(mode, 'a live playback mode includes happy');
  audio.configure(true, mode);
  audio.update({ expression: 'speaking', expression_cues_allowed: false });
  audio.update({ expression: 'happy', expression_cues_allowed: true });
  assert.deepEqual(played, []);
  now = 700;
  audio.update({ expression: 'happy', expression_cues_allowed: true });
  audio.update({ expression: 'happy', expression_cues_allowed: true });
  assert.deepEqual(played, ['/sfx/happy.wav']);
  audio.update({ expression: 'alert', expression_cues_allowed: false });
  assert.deepEqual(paused, ['/sfx/happy.wav']);
});
