'use strict';
const script = document.currentScript;
const siteRoot = new URL(script.dataset.siteRoot || '../', script.src);
const generatedToc = document.querySelector('[data-generate-toc]');
if (generatedToc) {
  document.querySelectorAll('.prose h2[id]').forEach(heading => {
    const link = document.createElement('a');
    link.href = '#' + heading.id;
    link.textContent = heading.textContent;
    generatedToc.append(link);
  });
}
const menu = document.querySelector('#menu');
menu.addEventListener('click', () => {
  const expanded = menu.getAttribute('aria-expanded') !== 'true';
  menu.setAttribute('aria-expanded', String(expanded));
  document.body.classList.toggle('menu-open', expanded);
});
document.querySelectorAll('pre').forEach(pre => {
  const button = document.createElement('button');
  button.className = 'copy'; button.type = 'button'; button.textContent = 'Copy';
  button.setAttribute('aria-label', 'Copy code');
  button.addEventListener('click', async () => {
    const text = pre.querySelector('code')?.textContent || '';
    try {
      if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text);
      else {
        const area = document.createElement('textarea'); area.value = text;
        document.body.append(area); area.select();
        const copied = document.execCommand('copy'); area.remove();
        if (!copied) throw new Error('copy unavailable');
      }
      button.textContent = 'Copied';
      document.querySelector('#announcement').textContent = 'Code copied';
    } catch { button.textContent = 'Select code to copy'; }
    setTimeout(() => { button.textContent = 'Copy'; }, 2500);
  });
  pre.append(button);
});
const dialog = document.querySelector('#search-dialog');
const input = document.querySelector('#search');
document.querySelector('#search-open').addEventListener('click', () => { dialog.showModal(); input.focus(); });
document.addEventListener('keydown', event => {
  if (event.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) {
    event.preventDefault(); dialog.showModal(); input.focus();
  }
});
input.addEventListener('input', () => {
  const results = document.querySelector('#search-results'); results.replaceChildren();
  const words = input.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  if (!words.length) return;
  const matches = (window.EVE_SEARCH || []).filter(item => words.every(word => (item.title+' '+item.text).toLowerCase().includes(word))).slice(0,12);
  if (!matches.length) { results.textContent = 'No results. Try a sensor name, stage number or error message.'; return; }
  for (const match of matches) {
    const link = document.createElement('a'); link.href = new URL(match.url, siteRoot).href;
    const title = document.createElement('strong'); title.textContent = match.title;
    const excerpt = document.createElement('span');
    const index = Math.max(0, match.text.toLowerCase().indexOf(words[0]) - 65);
    excerpt.textContent = match.text.slice(index,index+180).replace(/\s+/g,' ');
    link.append(title,excerpt); results.append(link);
  }
});
