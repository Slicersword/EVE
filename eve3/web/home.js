(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const token = new URLSearchParams(location.hash.slice(1)).get('token') || prompt('EVE control token') || '';
  history.replaceState(null, '', location.href.split('#')[0]);
  $('#back').href = '/control#' + encodeURIComponent(token);
  let epoch = null, available = false, snapshot = {}, lastStatus = 0, lastStop = -1;
  let musicURL = null, audioContext = null, analyser = null, level = null, wanted = false;
  let musicGeneration = 0, wasDucked = false, lastFace = '', polling = false, priorityBusy = false, voiceState = 'disabled';
  const media = $('#music');
  const note = s => { $('#notice').textContent = String(s || ''); };
  async function api(path, body, timeout = 4000) {
    const abort = new AbortController(), timer = setTimeout(() => abort.abort(), timeout);
    try {
      const r = await fetch(path, {method: body === undefined ? 'GET' : 'POST',
        headers: {'Content-Type': 'application/json', 'X-EVE-Token': token},
        body: body === undefined ? undefined : JSON.stringify(body), signal: abort.signal, cache: 'no-store'});
      if (!r.ok) throw Error('HTTP ' + r.status);
      return await r.json();
    } finally { clearTimeout(timer); }
  }
  async function command(name, body = {}) {
    if (!available && !['estop'].includes(name)) throw Error('Activity unavailable in this session');
    const start = epoch;
    const r = await api(name.startsWith('home.') ? '/api/home-command' : '/api/command', {name, args: body});
    if (start !== epoch || (!available && name !== 'estop')) throw Error('Private session changed');
    if (r.ok === false) throw Error(r.message || 'Request blocked');
    return r.message;
  }
  async function act(name, body = {}) {
    try { const r = await command(name, {lang: $('#lang').value, ...body}); note(r?.reply || (typeof r === 'string' ? r : 'Done.')); await refresh(); return r; }
    catch (e) { note(e.message); return null; }
  }
  function button(label, fn, parent) {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = label; b.onclick = fn; parent.appendChild(b); return b;
  }
  function saved(target, rows, kind, render, resume) {
    target.replaceChildren();
    rows.forEach(row => {
      const d = document.createElement('div'); d.className = 'saved';
      render(row, d);
      if (resume) button('Resume', () => act(resume, {action: 'resume_saved', id: row.id}), d);
      button('Delete', () => { if (confirm('Delete this saved entry?')) act('home.delete', {kind, id: row.id}); }, d);
      target.appendChild(d);
    });
  }
  function line(d, s) { const p = document.createElement('p'); p.textContent = s; d.appendChild(p); }
  function paint(v) {
    snapshot = v;
    const g = v.game;
    $('#gameView').textContent = g ? `${g.players[g.turn]} · ${g.paused ? 'Paused' : 'Playing'}\n${g.feedback || ''}\n${g.question || ''}\n${g.kind === 'twenty' ? g.questions + '/20 questions' : ''}\n${g.next_letter ? 'Next song letter: ' + g.next_letter : ''}` : 'Choose a game.';
    $('#gameOptions').replaceChildren(); $('#scores').replaceChildren();
    if (g) {
      (g.options || []).forEach((label, i) => button(label, () => act('home.game', {action: 'answer', choice: i}), $('#gameOptions')));
      g.players.forEach((p, i) => { const d = document.createElement('span'); d.textContent = `${p}: ${g.scores[i]} `;
        button('−', () => act('home.game', {action: 'score', team: i, delta: -1}), d);
        button('+', () => act('home.game', {action: 'score', team: i, delta: 1}), d); $('#scores').appendChild(d); });
    }
    const s = v.story;
    $('#storyView').textContent = s ? `${s.paused ? 'Paused\n' : ''}${s.recap ? 'Previously: ' + s.recap + '\n\n' : ''}${s.text}` : 'Choose your character and start.';
    $('#storyOptions').replaceChildren();
    if (s) s.choices.forEach((label, i) => button(label, () => act('home.story', {action: 'choose', choice: i}), $('#storyOptions')));
    saved($('#savedStories'), v.stories, 'story', (r, d) => line(d, r.value.title + ' · ' + r.value.hero), 'home.story');
    const k = v.kitchen;
    $('#kitchenView').textContent = k ? `${k.title} · Step ${k.index + 1}/${k.steps.length}${k.paused ? ' · Paused' : ''}\n${k.steps[k.index]}` : 'Enter your recipe.';
    saved($('#savedRecipes'), v.recipes, 'recipe', (r, d) => line(d, r.value.title), 'home.kitchen');
    saved($('#messages'), v.messages, 'message', (r, d) => { line(d, `${r.value.recipient} · ${r.value.read ? 'Read' : 'Unread'}\n${r.value.text}`);
      button('Mark read', () => act('home.messages', {action: 'read', id: r.id}), d);
      button('Correct', () => { const value = prompt('Correct this shared message:', r.value.text);
        if (value && confirm('Save the corrected message?')) act('home.messages', {action: 'save', id: r.id, recipient: r.value.recipient, text: value, expires: r.value.expires, confirm: true}); }, d);
    });
    saved($('#memories'), v.memories, 'capsule', (r, d) => {
      const label = document.createElement('label'), check = document.createElement('input'); check.type = 'checkbox'; check.dataset.memory = String(r.id);
      label.appendChild(check); label.appendChild(document.createTextNode(' ' + r.value.title + (r.value.date ? ' · ' + r.value.date : ''))); d.appendChild(label); line(d, r.value.text);
      button('Correct', () => { const value = prompt('Correct this memory:', r.value.text);
        if (value && confirm('Save the corrected memory?')) act('home.capsule', {action: 'save', id: r.id, ...r.value, text: value, confirm: true}); }, d);
    });
  }
  async function refresh() {
    if (!available) return;
    const start = epoch;
    try { const v = await command('home.view'); if (start === epoch && available) paint(v); }
    catch(e) { note(e.message); }
  }
  $('#refresh').onclick = refresh;
  $('#gameStart').onclick = () => act('home.game', {action: 'start', kind: $('#gameKind').value, players: $('#players').value.split(',').map(s => s.trim()).filter(Boolean)});
  document.querySelectorAll('[data-game]').forEach(b => b.onclick = () => act('home.game', {action: b.dataset.game}));
  $('#guessSubmit').onclick = () => act('home.game', snapshot.game?.kind === 'antakshari' ? {action: 'answer', title: $('#guess').value} : {action: 'guess', guess: $('#guess').value});
  $('#askTrait').onclick = () => act('home.game', {action: 'question', question: $('#question').value});
  $('#storyStart').onclick = () => act('home.story', {action: 'start', hero: $('#hero').value});
  $('#storySave').onclick = () => { if (confirm('Save this character/story and keep future choices locally?')) act('home.story', {action: 'save', confirm: true}); };
  $('#storyPause').onclick = () => act('home.story', {action: 'pause'});
  $('#storyResume').onclick = () => act('home.story', {action: 'resume'});
  function speak(s, lang) { if (s) act('say', {text: s.slice(0, 300), lang: (lang || $('#lang').value).split('-')[0]}); }
  $('#storySpeak').onclick = () => speak(snapshot.story?.speech_text || snapshot.story?.text, snapshot.story?.lang);
  $('#recipeStart').onclick = () => act('home.kitchen', {action: 'start', title: $('#recipeTitle').value, steps: $('#recipeSteps').value.split('\n').map(s => s.trim()).filter(Boolean)});
  $('#recipeSave').onclick = () => { if (confirm('Save this recipe and its progress locally?')) act('home.kitchen', {action: 'save', confirm: true}); };
  document.querySelectorAll('[data-kitchen]').forEach(b => b.onclick = () => act('home.kitchen', {action: b.dataset.kitchen}));
  $('#stepSpeak').onclick = () => speak(snapshot.kitchen?.steps[snapshot.kitchen.index], snapshot.kitchen?.lang);
  $('#timerStart').onclick = async () => { const r = await act('home.timer', {name: $('#timerName').value, seconds: Number($('#timerSeconds').value)}); if (r) timers(); };
  async function timers() {
    try { const r = await command('home.timers'); $('#timers').replaceChildren();
      r.items.forEach(t => { const d = document.createElement('div'); d.className = 'saved'; line(d, `${t.text} · ${new Date(t.due * 1000).toLocaleString()}${t.due * 1000 < Date.now() ? ' · DUE' : ''}`);
        button('Done', async () => { await act('home.timer_cancel', {id: t.id}); timers(); }, d);
        button('Cancel', async () => { await act('home.timer_cancel', {id: t.id}); timers(); }, d); $('#timers').appendChild(d); });
    } catch(e) { note(e.message); }
  }
  $('#timersRefresh').onclick = timers;
  $('#messageSave').onclick = async () => {
    if (!confirm('Save this message on the shared household board?\n\n' + $('#messageText').value)) return;
    const hours = Number($('#messageHours').value);
    const r = await act('home.messages', {action: 'save', recipient: $('#recipient').value, text: $('#messageText').value, expires: hours ? Date.now()/1000 + hours*3600 : 0, confirm: true});
    if (r) $('#messageText').value = '';
  };
  $('#memorySave').onclick = async () => {
    if (!confirm('Keep this memory locally?\n\n' + $('#memoryText').value)) return;
    const r = await act('home.capsule', {action: 'save', title: $('#memoryTitle').value, text: $('#memoryText').value, date: $('#memoryDate').value, category: $('#memoryCategory').value, confirm: true});
    if (r) $('#memoryText').value = '';
  };
  $('#memoryRecap').onclick = async () => {
    try { const ids = [...document.querySelectorAll('[data-memory]:checked')].map(e => Number(e.dataset.memory));
      const r = await command('home.capsule', {action: 'recap', ids}); $('#recap').textContent = r.reply; }
    catch(e) { note(e.message); }
  };
  $('#eraseHome').onclick = () => { if (confirm('Erase saved home stories, recipes, messages and memories? Existing reminder timers are managed separately.')) act('home.erase', {confirm: 'ERASE HOME DATA'}); };
  function pauseMusic(clear = false) { media.pause(); if (clear) { wanted = false; media.currentTime = 0; musicGeneration++; } }
  $('#quiet').onclick = () => { pauseMusic(true); };
  $('#stop').onclick = () => { pauseMusic(true); act('estop'); };
  $('#musicPause').onclick = () => { wanted = false; musicGeneration++; media.pause(); };
  $('#musicStop').onclick = () => { pauseMusic(true); act('home.music_stop'); };
  $('#musicFile').onchange = () => {
    pauseMusic(true); if (musicURL) URL.revokeObjectURL(musicURL); musicURL = null; media.removeAttribute('src');
    const f = $('#musicFile').files[0];
    if (!f || f.size > 100 * 1024 * 1024 || !/\.(wav|mp3|ogg|flac|m4a)$/i.test(f.name)) { note('Choose a local audio file up to 100 MB.'); return; }
    musicURL = URL.createObjectURL(f); media.src = musicURL;
  };
  $('#musicPlay').onclick = async () => {
    if (!available || Date.now() - lastStatus > 1800 || !musicURL) { note('Choose music and reconnect to EVE first.'); return; }
    try {
      const state = await api('/api/audio-priority', undefined, 700);
      if (!state.home_available || state.stop_latched || state.capture_active) { note('Music is paused while the microphone, sleep or STOP is active.'); return; }
    } catch { note('Reconnect to EVE before playing music.'); return; }
    const playEpoch = epoch, generation = ++musicGeneration;
    try {
      if (!audioContext) { audioContext = new AudioContext(); analyser = audioContext.createAnalyser(); analyser.fftSize = 256;
        const source = audioContext.createMediaElementSource(media); source.connect(analyser); analyser.connect(audioContext.destination); level = new Uint8Array(analyser.frequencyBinCount); }
      await audioContext.resume();
      if (!available || epoch !== playEpoch || generation !== musicGeneration) return;
      wanted = true; media.volume = Number($('#musicVolume').value)/100; await media.play();
      if (!available || epoch !== playEpoch || generation !== musicGeneration) media.pause();
    } catch(e) { wanted = false; note('Playback unavailable: ' + e.message); }
  };
  media.onended = () => { wanted = false; };
  let snapshotCapture = false;
  async function priority() {
    if (priorityBusy) return; priorityBusy = true;
    try {
      const r = await api('/api/audio-priority', undefined, 700);
      const blocked = !available || !r.home_available || r.stop_latched || Date.now() - lastStatus > 1800;
      snapshotCapture = !!r.capture_active;
      const captureBlocks = snapshotCapture;
      const hearing = ['conversation','transcribing'].includes(voiceState);
      if (blocked || captureBlocks) { pauseMusic(true); }
      else if (hearing) { media.pause(); wasDucked = true; if (!$('#musicResume').checked) wanted = false; }
      else if (r.speaking) { media.volume = Number($('#musicVolume').value)/100 * .15; wasDucked = true; }
      else { media.volume = Number($('#musicVolume').value)/100;
        if (wasDucked && wanted && $('#musicResume').checked && media.paused) {
          const generation = musicGeneration; media.play().then(() => { if (generation !== musicGeneration || !available) media.pause(); }).catch(() => { wanted = false; });
        } wasDucked = false; }
    } catch(e) { pauseMusic(true); } finally { priorityBusy = false; }
  }
  function clearPrivate() {
    snapshot = {}; note(''); pauseMusic(true);
    if (musicURL) URL.revokeObjectURL(musicURL);
    musicURL = null; media.removeAttribute('src'); media.load(); $('#musicFile').value = '';
    for (const id of ['gameView','gameOptions','scores','storyView','storyOptions','savedStories','savedRecipes','kitchenView','messages','memories','recap','timers']) $('#'+id).replaceChildren();
    for (const id of ['hero','guess','players','recipeTitle','recipeSteps','recipient','messageText','memoryTitle','memoryText','memoryDate','timerName']) $('#'+id).value = '';
    $('#privateViews').hidden = true;
  }
  async function poll() {
    if (polling) return; polling = true;
    try {
      const s = await api('/api/audio-priority', undefined, 1200), next = s.session;
      const can = s.home_available === true;
      if (epoch !== null && (epoch !== next || !can)) clearPrivate();
      const first = epoch !== next || !available;
      epoch = next; available = can; lastStatus = Date.now();
      voiceState = s.capture_active ? 'conversation' : 'disabled';
      const generation = s.music_stop_generation;
      if (lastStop !== -1 && generation !== lastStop) pauseMusic(true); lastStop = generation;
      $('#connection').textContent = can ? 'Local connection · ready' : 'Activities hidden · owner/awake mode required';
      $('#audioState').textContent = 'Turn-taking · music pauses when microphone capture is enabled.';
      $('#privateViews').hidden = !can;
      if (can && first) await refresh();
    } catch(e) { available = false; clearPrivate(); $('#connection').textContent = 'Connection lost · media paused'; }
    finally { polling = false; }
  }
  function animate() {
    if (analyser && !media.paused && available) { analyser.getByteFrequencyData(level); const rms = level.reduce((a,b) => a+b,0)/level.length/255;
      const face = rms > .12 ? 'speaking' : 'happy'; if (face !== lastFace) { $('#musicFace').innerHTML = window.EvaFaceArt.svg(face); lastFace = face; }
      $('#musicFace').style.transform = `scale(${1 + Math.min(.06,rms*.1)}) rotate(${Math.sin(media.currentTime*3)*rms*3}deg)`;
    } else { $('#musicFace').style.transform = ''; if (lastFace !== 'idle') { $('#musicFace').innerHTML = window.EvaFaceArt.svg('idle'); lastFace = 'idle'; } }
  }
  window.addEventListener('pagehide', () => { pauseMusic(true); if (musicURL) URL.revokeObjectURL(musicURL); });
  document.addEventListener('visibilitychange', () => { if(document.hidden) pauseMusic(true); });
  poll(); setInterval(poll, 1000); setInterval(priority, 200); setInterval(animate, 100);
})();
