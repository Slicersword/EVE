#!/usr/bin/env node
/** Build an offline documentation site from tracked Markdown and source. No npm install needed. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { Marked, Renderer } from './vendor/marked.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
if (args.length && !(args.length === 2 && args[0] === '--output')) {
  throw new Error('Usage: node tools/build_docs.mjs [--output DIRECTORY]');
}
const output = path.resolve(root, args[1] || 'dist');
// Output cleanup must never remove source, private files, or an enclosing directory.
if (output !== path.join(root, 'dist')) throw new Error('Build to this checkout’s dist directory only');
const sections = JSON.parse(fs.readFileSync(path.join(root, '_data/navigation.json'), 'utf8'));
const esc = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const slug = s => s.toLowerCase().replace(/<[^>]*>/g, '').replace(/[^\p{L}\p{N} _-]/gu, '').replace(/\s+/g, '-');
const route = source => source === 'README.md' ? 'index.html' : source.replace(/\.md$/i, '.html');
const relative = (from, to) => path.posix.relative(path.posix.dirname(from), to) || path.posix.basename(to);
const files = dir => fs.readdirSync(path.join(root, dir), { withFileTypes: true }).flatMap(e => {
  const name = path.posix.join(dir, e.name);
  return e.isDirectory() ? files(name) : [name];
});
const docs = ['README.md', 'CONTRIBUTING.md', 'SECURITY.md', 'CHANGELOG.md', ...files('docs').filter(f => f.endsWith('.md'))];
const snapshot = JSON.parse(fs.readFileSync(path.join(root, '_data/source_files.json'), 'utf8'));
const sources = Object.keys(snapshot).sort();
for (const source of sources) {
  if (fs.readFileSync(path.join(root, source), 'utf8') !== snapshot[source]) {
    throw new Error('Source viewer is stale. Run python3 tools/build_source_index.py');
  }
}
const sourceRoute = source => `source/${source}.html`;
let revision = process.env.EVE_DOCS_REVISION || 'working-tree';
if (revision === 'working-tree') {
  try { revision = execFileSync('git', ['rev-parse', '--short=12', 'HEAD'], {cwd: root, encoding:'utf8', stdio:['ignore','pipe','ignore']}).trim(); } catch {}
}
const searchIndex = [];
fs.rmSync(output, { recursive: true, force: true });
fs.mkdirSync(output, { recursive: true });
fs.cpSync(path.join(root, 'site/assets'), path.join(output, 'assets'), {recursive: true});
fs.cpSync(path.join(root, 'docs/assets'), path.join(output, 'docs/assets'), {recursive: true});
fs.writeFileSync(path.join(output, '.nojekyll'), '');

function write(url, text) {
  const dest = path.join(output, url);
  fs.mkdirSync(path.dirname(dest), {recursive:true});
  fs.writeFileSync(dest, text);
}

function shell(url, title, body, toc = [], source = '') {
  const link = target => esc(relative(url, target));
  const nav = sections.map(([label, links]) => `<div class="nav-group"><p>${label}</p>${links.map(([target,, name]) => `<a href="${link(target)}"${url === target ? ' aria-current="page"' : ''}>${esc(name)}</a>`).join('')}</div>`).join('');
  const ordered = sections.flatMap(([, links]) => links);
  const index = ordered.findIndex(([target]) => target === url);
  const prev = ordered[index-1], next = index >= 0 ? ordered[index+1] : null;
  const pager = index >= 0 ? `<nav class="pager" aria-label="Continue reading">${prev ? `<a href="${link(prev[0])}"><small>Previous</small>${esc(prev[2])}</a>` : '<span></span>'}${next ? `<a href="${link(next[0])}"><small>Next</small>${esc(next[2])}</a>` : ''}</nav>` : '';
  const edit = source ? `<a href="https://github.com/Slicersword/EVE/blob/main/${esc(source)}">View on GitHub</a>` : '';
  const intro = url === 'index.html' ? `<div class="hero"><p class="eyebrow">A robot you build. A guide you can follow.</p><h1>Bring EVE<br><em>to life.</em></h1><p>Build a local-first home companion, one clear step at a time. From your first wire to your first conversation.</p><div class="hero-actions"><a class="primary" href="${link('docs/GETTING_STARTED.html')}">Start building</a><a href="${link('docs/HARDWARE.html')}">Explore the hardware</a></div><div class="platforms"><span>Raspberry Pi 4</span><span>Arduino Mega</span><span>Local voice</span><span>Open documentation</span></div><svg class="robot" viewBox="0 0 220 185" role="img" aria-label="EVE robot illustration"><rect x="32" y="4" width="156" height="100" rx="26" fill="#111f2e" stroke="#639bba" stroke-width="2"/><rect x="49" y="19" width="122" height="67" rx="17" fill="#08121d"/><path d="M69 43 Q80 34 91 43 M129 43 Q140 34 151 43" stroke="#70e5cb" stroke-width="8" fill="none" stroke-linecap="round"/><path d="M96 64 Q110 76 124 64" stroke="#70e5cb" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M101 104V119h18v-15" stroke="#639bba" stroke-width="2" fill="#162b3b"/><rect x="39" y="119" width="142" height="43" rx="13" fill="#162b3b" stroke="#639bba" stroke-width="2"/><rect x="24" y="136" width="24" height="45" rx="9" fill="#07121e" stroke="#639bba"/><rect x="172" y="136" width="24" height="45" rx="9" fill="#07121e" stroke="#639bba"/><circle cx="110" cy="140" r="5" fill="#70e5cb"/></svg></div><div class="guide-note"><strong>Start from zero.</strong> No saved progress or pre-built robot required. Confirm your parts, follow the stages, and test each step.</div>` : '';
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${esc(title)} · Build EVE</title><meta name="description" content="Step-by-step EVE robot build documentation, wiring, software, calibration and troubleshooting."><link rel="stylesheet" href="${link('assets/style.css')}"><link rel="icon" href="${link('assets/icon.svg')}" type="image/svg+xml"></head><body><a class="skip" href="#main">Skip to content</a><header class="top"><a class="brand" href="${link('index.html')}"><span class="brand-mark">e</span> EVE <span class="brand-sub">/ build manual</span></a><div class="top-actions"><button id="search-open" type="button">Search guide <kbd>/</kbd></button><a data-progress-summary href="${link('docs/PROGRESS.html')}">My build progress</a><a href="https://github.com/Slicersword/EVE">GitHub</a><button id="menu" aria-expanded="false" aria-controls="sidebar" type="button">Menu</button></div></header><aside id="sidebar" class="sidebar" aria-label="Documentation">${nav}<div class="side-foot">Built from the repository.<br>Offline guide. Optional local progress.</div></aside><div class="workspace"><main id="main" tabindex="-1">${intro}<div class="page-meta"><span>BUILD MANUAL</span>${edit}</div><article class="prose">${body}</article>${pager}<footer>Build EVE · Repository revision <code>${esc(revision)}</code><br>Software checks and physical acceptance are separate. Test your own build.</footer></main><aside class="on-this-page"><p>On this page</p>${toc.filter(x => x.depth === 2).map(x => `<a href="#${esc(x.id)}">${esc(x.text)}</a>`).join('')}<a class="top-link" href="#main">Back to top</a></aside></div><dialog id="search-dialog"><form method="dialog"><label for="search">Find a step, command or fix</label><button class="close" aria-label="Close search">Close</button></form><input id="search" type="search" placeholder="Try: I2C, firmware, microphone…" autocomplete="off"><div id="search-results" aria-live="polite"></div></dialog><div id="announcement" class="sr-only" aria-live="polite"></div><script src="${link('assets/search-data.js')}"></script><script src="${link('assets/site.js')}"></script><script src="${link('assets/progress-state.js')}"></script><script src="${link('assets/progress-data.js')}"></script><script src="${link('assets/progress.js')}"></script></body></html>`;
}

for (const source of docs) {
  const url = route(source), text = fs.readFileSync(path.join(root, source), 'utf8'), toc = [], ids = new Map();
  const renderer = new Renderer();
  renderer.heading = function({tokens, depth}) {
    const html = this.parser.parseInline(tokens), plain = html.replace(/<[^>]*>/g, '');
    const base = slug(plain), count = ids.get(base) || 0;
    ids.set(base, count+1);
    const id = count ? `${base}-${count}` : base;
    toc.push({depth, id, text:plain});
    return `<h${depth} id="${esc(id)}">${html}</h${depth}>\n`;
  };
  renderer.link = function({href, title, tokens}) {
    let target = href;
    if (!/^(?:[a-z]+:|\/|#)/i.test(href)) {
      const [filename, fragment] = href.split('#');
      const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(source), filename));
      if (docs.includes(resolved)) target = relative(url, route(resolved));
      else if (sources.includes(resolved)) target = relative(url, sourceRoute(resolved));
      else throw new Error(`Unmapped documentation link ${source}: ${href}`);
      if (fragment) target += '#' + fragment;
    }
    return `<a href="${esc(target)}"${title ? ` title="${esc(title)}"` : ''}>${this.parser.parseInline(tokens)}</a>`;
  };
  const markdown = new Marked({renderer, gfm:true});
  const body = markdown.parse(text), title = toc[0]?.text || source;
  write(url, shell(url, title, body, toc, source));
  searchIndex.push({url, title, text:text.replace(/[`#*|]/g, '')});
  write(`markdown/${source}`, text);
}
const listing = `<h1>Every line, in one place.</h1><p>The source below is copied directly from this repository at build time. Open any file to read its complete contents or download the raw file. Private settings, runtime data and model weights are excluded.</p><ul class="source-list">${sources.map(source => `<li><a href="${esc(sourceRoute(source))}">${esc(source)}</a></li>`).join('')}</ul>`;
write('code.html', shell('code.html', 'Source code', listing));
for (const source of sources) {
  const text = fs.readFileSync(path.join(root, source), 'utf8'), url = sourceRoute(source);
  write(`raw/${source}`, text);
  write(url, shell(url, source, `<p><a href="${esc(relative(url,'code.html'))}">All source files</a></p><h1 class="source-title">${esc(source)}</h1><p><a download href="${esc(relative(url,`raw/${source}`))}">Download raw file</a></p><pre><code>${esc(text)}</code></pre>`, [], source));
}
// Classic script works on file:// as well as on an HTTP host. No fetch or CDN is required.
write('assets/search-data.js', `window.EVE_SEARCH=${JSON.stringify(searchIndex).replaceAll('<', '\\u003c')};\n`);
write('assets/progress-data.js', 'window.EVE_BUILD_PROGRESS=' + fs.readFileSync(path.join(root, '_data/build_progress.json'), 'utf8').trim() + ';\n');
write('build-info.json', JSON.stringify({revision, documents:docs.length, source_files:sources.length},null,2)+'\n');
console.log(`Built ${docs.length} documents and ${sources.length} source listings in ${output}`);
