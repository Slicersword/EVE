/* Browser-local build notebook. It never reads or changes the robot. */
(function (root, factory) {
  'use strict';
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.EveProgress = factory();
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const KEY = 'eve-build-progress:v1';
  const MAX_BYTES = 250000;
  const MAX_NOTE = 2000;
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  function ids(manifest) { return manifest.groups.flatMap(group => group.tasks.map(task => task.id)); }
  function empty() { return {schemaVersion: 1, project: 'EVE', enabled: false, tasks: {}}; }
  function validate(value, manifest) {
    if (!object(value) || value.schemaVersion !== 1 || value.project !== 'EVE' ||
        typeof value.enabled !== 'boolean' || !object(value.tasks)) {
      throw new Error('Choose an EVE progress backup (schema version 1).');
    }
    const known = new Set(ids(manifest));
    const result = empty(); result.enabled = value.enabled;
    for (const [id, task] of Object.entries(value.tasks)) {
      if (!known.has(id)) throw new Error('This backup contains an unknown task: ' + id);
      if (!object(task) || typeof task.done !== 'boolean' || typeof task.note !== 'string' ||
          task.note.length > MAX_NOTE || !(task.completedAt === null ||
          (typeof task.completedAt === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(task.completedAt) &&
           Number.isFinite(Date.parse(task.completedAt))))) {
        throw new Error('Invalid task record: ' + id);
      }
      result.tasks[id] = {done: task.done, note: task.note, completedAt: task.done ? task.completedAt : null};
    }
    return result;
  }
  function parse(text, manifest) {
    if (typeof text !== 'string' || text.length > MAX_BYTES) throw new Error('Backup is too large (250 KB maximum).');
    return validate(JSON.parse(text), manifest);
  }
  function update(state, manifest, id, changes, now = new Date().toISOString()) {
    if (!ids(manifest).includes(id)) throw new Error('Unknown build task.');
    const next = validate(state, manifest);
    const previous = own(next.tasks, id) ? next.tasks[id] : {done: false, note: '', completedAt: null};
    const record = {...previous, ...changes};
    record.completedAt = record.done ? (previous.done ? previous.completedAt : now) : null;
    next.tasks[id] = record;
    return validate(next, manifest);
  }
  function summary(state, manifest) {
    const tasks = manifest.groups.flatMap(group => group.tasks);
    const done = tasks.filter(task => own(state.tasks, task.id) && state.tasks[task.id].done).length;
    return {done, total: tasks.length, percent: tasks.length ? Math.round(done / tasks.length * 100) : 0,
      next: tasks.find(task => !own(state.tasks, task.id) || !state.tasks[task.id].done) || null};
  }
  function notebook(storage, manifest) {
    let state = empty(), warning = '', persistent = Boolean(storage), blocked = false;
    if (storage) {
      try {
        const saved = storage.getItem(KEY);
        if (saved !== null) state = parse(saved, manifest);
      } catch {
        // Preserve an unreadable backup instead of silently overwriting it on the next click.
        warning = 'Saved progress could not be read. Import a valid backup or reset to start again.';
        persistent = false; blocked = true;
      }
    }
    function save(next) {
      state = validate(next, manifest);
      if (!blocked && storage) {
        try { storage.setItem(KEY, JSON.stringify(state)); persistent = true; warning = ''; }
        catch { persistent = false; warning = 'Browser storage is unavailable. Export a backup before closing this page.'; }
      }
      return state;
    }
    return {
      get state() { return validate(state, manifest); },
      get persistent() { return persistent; },
      get warning() { return warning; },
      enable(value) { return save({...state, enabled: value}); },
      update(id, changes) { return save(update(state, manifest, id, changes)); },
      export() { return JSON.stringify({...state, exportedAt: new Date().toISOString()}, null, 2) + '\n'; },
      import(text) { const next = parse(text, manifest); blocked = false; return save(next); },
      reset() { blocked = false; return save(empty()); },
    };
  }
  return {KEY, MAX_BYTES, MAX_NOTE, empty, validate, parse, update, summary, notebook};
}));
