# The repository and companion website

The website is generated from the repository's Markdown and full source files.
It uses static HTML, CSS, a local Markdown renderer and browser JavaScript. There
is no backend, database, analytics, account requirement, paid API or external font/CDN.
It includes navigation, offline search, code-copy buttons, source downloads and mobile layouts.

## Build once and use offline

Install Node.js 22 (the CI target) and Python 3.11+ on a development computer.
From the repository root:

```bash
node tools/build_docs.mjs
python3 tools/check_site.py
```

Open `dist/index.html` in a browser. Keep the complete `dist/` directory together;
it contains every page and asset. Search works from `file://` without a server.
If your browser blocks clipboard access to local files, select/copy the code manually.
You can copy the directory to the Pi or a USB drive. Internet is still needed for
initial package/model downloads described by the robot installer.

For an ordinary local HTTP preview on your development computer:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:8000`, then Ctrl+C to stop. This is a documentation server,
separate from the robot's control API. Never enter runtime tokens into the docs site.

## Free automatic hosting with GitHub Pages

The repository includes a Pages workflow. To enable it once as the repository administrator:

1. Open repository **Settings → Pages** and choose **GitHub Actions** as the build source.
2. In **Settings → Secrets and variables → Actions → Variables**, add repository variable
   `EVE_DEPLOY_PAGES` with the exact value `true`. No secret is required.
3. Run **Actions → Publish build guide → Run workflow**, or push a change to `main`.
4. Read the deployed URL from the successful deployment job. A planned URL is not proof
   that Pages is enabled or deployed; check the workflow result.

Once enabled, each push regenerates and validates the guide before deployment. All
paths are relative, so a repository subpath works. GitHub's account/repository eligibility
and service limits apply; public repository Pages is the intended free target.
Setting the variable to `false` stops future deployments but does not delete an existing site.

The verification workflow always builds an `eve-documentation-offline` artifact.
Download it from a successful run, extract it, and open its `index.html` when online
hosting is not enabled. Another static host can serve the same generated directory.

## Update without documentation drift

Edit ordinary pages under `docs/` and the root README. For the generated software
guide, edit `tools/setup_steps.py`, `tools/stage.py` or `docs/setup/` instead, then:

```bash
python3 tools/stage.py guide > docs/SETUP_GUIDE.md
python3 tools/check_repo.py
node tools/build_docs.mjs
python3 tools/check_site.py
```

Never hand-edit generated `dist/` output. The build includes a repository revision
in the footer and `build-info.json`, and copies source listings directly from the
same checkout. Private `config/local.json`, runtime data, tokens and model weights
are excluded. A manually hosted mirror must be rebuilt and republished after changes;
GitHub Pages provides the automatic push-to-site path.

## Third-party attribution

The build vendors Marked 17.0.5 under MIT; its license is retained in `tools/vendor/`.
The robot and documentation's project license has not yet been selected by the maintainer.
