(function () {
  'use strict';
  const source = window.EVE_SOURCE, container = document.querySelector('#source-browser');
  if (!source || !container) return;
  const input = container.querySelector('input'), select = container.querySelector('select');
  const code = container.querySelector('code'), title = container.querySelector('[data-source-path]');
  const count = container.querySelector('[data-source-count]'), download = container.querySelector('button');
  const files = Object.keys(source).sort();
  let current = files.includes('eve') ? 'eve' : files[0];
  try {
    const requested = decodeURIComponent(location.hash.slice(1));
    if (files.includes(requested)) current = requested;
  } catch { /* An invalid bookmark does not stop the viewer. */ }
  function show(name) {
    if (!Object.prototype.hasOwnProperty.call(source, name)) return;
    current = name; title.textContent = name; code.textContent = source[name];
    select.value = name; download.disabled = false;
    history.replaceState(null, '', '#' + encodeURIComponent(name));
  }
  function filter() {
    const query = input.value.trim().toLowerCase();
    const matches = files.filter(name => name.toLowerCase().includes(query));
    select.replaceChildren();
    for (const name of matches) {
      const option = document.createElement('option'); option.value = name; option.textContent = name;
      select.append(option);
    }
    count.textContent = `${matches.length} of ${files.length} public source files`;
    select.disabled = matches.length === 0;
    if (!matches.length) {
      title.textContent = 'No matching files'; code.textContent = 'Try a folder name such as firmware, eve3, config or tools.';
      download.disabled = true;
    } else show(matches.includes(current) ? current : matches[0]);
  }
  input.addEventListener('input', filter);
  select.addEventListener('change', () => show(select.value));
  download.addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([source[current]], {type: 'text/plain;charset=utf-8'}));
    const link = document.createElement('a'); link.href = url; link.download = current.split('/').pop();
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  filter();
}());
