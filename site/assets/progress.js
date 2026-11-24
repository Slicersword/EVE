(function () {
  'use strict';
  const core = window.EveProgress, manifest = window.EVE_BUILD_PROGRESS;
  if (!core || !manifest) return;
  const script = document.currentScript;
  const root = new URL(script.dataset.siteRoot || '../', script.src);
  let storage;
  try { storage = window.localStorage; } catch { storage = null; }
  const book = core.notebook(storage, manifest);
  const container = document.querySelector('#build-progress');
  const shortcuts = document.querySelectorAll('[data-progress-summary]');
  function announce(message) {
    const region = document.querySelector('#announcement');
    if (region) region.textContent = message;
  }
  function shortcut() {
    const summary = core.summary(book.state, manifest);
    shortcuts.forEach(link => { link.textContent = book.state.enabled ?
      `My build: ${summary.done}/${summary.total} · ${summary.percent}%` : 'My build progress'; });
  }
  shortcut();
  if (!container) return;
  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function button(text, action, className) {
    const node = element('button', text, className); node.type = 'button';
    node.addEventListener('click', action); return node;
  }
  let filter = 'all';
  const controls = element('div', undefined, 'progress-controls');
  const toggle = button('', () => { book.enable(!book.state.enabled); refresh(); });
  const exportButton = button('Export backup', () => {
    const url = URL.createObjectURL(new Blob([book.export()], {type: 'application/json'}));
    const link = element('a'); link.href = url;
    link.download = 'eve-build-progress-' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    announce('Progress backup downloaded. Keep it somewhere you can find again.');
  });
  const file = element('input'); file.type = 'file'; file.accept = '.json,application/json';
  file.className = 'sr-only'; file.id = 'progress-import'; file.setAttribute('aria-label', 'Choose progress backup');
  const importButton = button('Import backup', () => file.click());
  const message = element('p', '', 'progress-message'); message.setAttribute('role', 'status');
  file.addEventListener('change', async () => {
    const selected = file.files[0]; if (!selected) return;
    try {
      if (selected.size > core.MAX_BYTES) throw new Error('Backup is too large (250 KB maximum).');
      const text = await selected.text();
      core.parse(text, manifest); // Validate completely before asking to replace the current notebook.
      if (!window.confirm('Replace the progress and notes in this browser with this backup? Export your current progress first if you need it.')) return;
      book.import(text); refresh(); message.textContent = 'Backup imported.';
    } catch (error) { message.textContent = 'Import failed: ' + error.message; }
    finally { file.value = ''; }
  });
  const reset = button('Reset progress', () => {
    if (window.confirm('Clear all build checkmarks and notes in this browser? This cannot be undone without an exported backup.')) {
      book.reset(); refresh(); message.textContent = 'Progress reset. Nothing is marked complete.';
    }
  });
  controls.append(toggle, exportButton, importButton, reset, file);
  const status = element('p', '', 'progress-storage');
  const summary = element('div', undefined, 'progress-overview');
  const count = element('strong');
  const bar = element('progress'); bar.max = 100; bar.setAttribute('aria-label', 'Build tasks completed');
  const next = element('p');
  summary.append(count, bar, next);
  const filters = element('div', undefined, 'progress-filters'); filters.setAttribute('aria-label', 'Filter tasks');
  const filterButtons = [['all', 'All tasks'], ['remaining', 'Remaining'], ['done', 'Completed']].map(([value, label]) => {
    const node = button(label, () => { filter = value; refresh(); });
    filters.append(node); return [value, node];
  });
  const tasks = element('div');
  const rows = [];
  for (const group of manifest.groups) {
    const section = element('section', undefined, 'progress-group');
    const heading = element('h2', group.title); heading.id = 'progress-' + group.id;
    const groupCount = element('span', '', 'progress-group-count'); heading.append(groupCount);
    const list = element('ul', undefined, 'progress-task-list');
    for (const task of group.tasks) {
      const row = element('li', undefined, 'progress-task');
      const label = element('label', undefined, 'progress-task-label');
      const checkbox = element('input'); checkbox.type = 'checkbox'; checkbox.id = 'task-' + task.id;
      const title = element('span', task.title); label.append(checkbox, title);
      const detail = element('p', task.detail);
      const link = element('a', 'Open instructions'); link.href = new URL(task.href, root).href;
      const details = element('details'); const notesLabel = element('summary', 'Notes and measurements');
      const areaLabel = element('label', 'Your notes (saved in this browser)'); areaLabel.htmlFor = 'note-' + task.id;
      const area = element('textarea'); area.id = 'note-' + task.id; area.rows = 3;
      area.maxLength = core.MAX_NOTE; area.placeholder = 'Record a model, reading, result or next action. Keep passwords and tokens out.';
      const completed = element('small');
      const saveNote = () => {
        book.update(task.id, {note: area.value}); refresh(false);
      };
      area.addEventListener('input', saveNote);
      checkbox.addEventListener('change', () => {
        book.update(task.id, {done: checkbox.checked}); refresh();
        announce(task.title + (checkbox.checked ? ' marked complete.' : ' marked incomplete.'));
      });
      details.append(notesLabel, areaLabel, area, completed);
      row.append(label, detail, link, details); list.append(row);
      rows.push({task, group: group.id, row, checkbox, area, completed});
    }
    section.append(heading, list); tasks.append(section);
    groupCount.dataset.group = group.id;
  }
  container.replaceChildren(controls, status, summary, filters, message, tasks);
  function refresh(updateInputs = true) {
    const state = book.state, stats = core.summary(state, manifest);
    toggle.textContent = state.enabled ? 'Pause tracking' : 'Start tracking on this device';
    toggle.classList.toggle('progress-primary', !state.enabled);
    status.textContent = book.warning || (book.persistent ?
      'Saved only in this browser. Export a backup to move devices or protect against cleared browser data.' :
      'Session only: browser storage is unavailable. Export before closing this page.');
    if (!state.enabled) status.textContent += ' Tracking is paused; your saved checkmarks and notes are kept.';
    count.textContent = `${stats.done} of ${stats.total} tasks complete · ${stats.percent}%`;
    bar.value = stats.percent;
    next.replaceChildren();
    if (stats.next) {
      next.append('Next unfinished task: ');
      const link = element('a', stats.next.title); link.href = new URL(stats.next.href, root).href; next.append(link);
    } else next.textContent = 'All website checklist items are recorded. Finish the robot’s own acceptance checks before operating it.';
    for (const row of rows) {
      const record = state.tasks[row.task.id] || {done: false, note: '', completedAt: null};
      row.checkbox.checked = record.done; row.checkbox.disabled = !state.enabled;
      row.area.disabled = !state.enabled;
      if (updateInputs) row.area.value = record.note;
      row.row.classList.toggle('task-done', record.done);
      row.row.hidden = filter === 'remaining' && record.done || filter === 'done' && !record.done;
      row.completed.textContent = record.completedAt ? 'Recorded: ' + new Date(record.completedAt).toLocaleString() : 'Not marked complete';
    }
    document.querySelectorAll('[data-group]').forEach(node => {
      const groupRows = rows.filter(row => row.group === node.dataset.group);
      node.textContent = ` ${groupRows.filter(row => row.checkbox.checked).length}/${groupRows.length}`;
      node.closest('section').hidden = groupRows.every(row => row.row.hidden);
    });
    filterButtons.forEach(([value, node]) => node.setAttribute('aria-pressed', String(filter === value)));
    shortcut();
  }
  refresh();
}());
