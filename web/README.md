# tokenscape web

Browser build of tokenscape. The page runs the same analysis code as the CLI inside
[Pyodide](https://pyodide.org) (Python compiled to WebAssembly), in a Web Worker. The sessions
zip is read in the browser tab and never uploaded; the page's Content-Security-Policy only
allows network requests back to this site.

Nothing here is part of the PyPI package or the CLI install.

## Build and run locally

Requires Node 22+ and [uv](https://docs.astral.sh/uv/).

```bash
bash web/build.sh                      # → web/dist (page + self-hosted Pyodide + wheel from this checkout)
node web/smoke.mjs [bundle.zip]        # runs the built wheel in Pyodide under Node
python3 -m http.server -d web/dist     # open http://localhost:8000
```

## Layout

| File | Role |
| --- | --- |
| `index.html`, `style.css`, `app.js` | Page: file picker, period, report iframe, downloads |
| `worker.js` | Loads Pyodide and the wheel, calls `tokenscape.webapp.build_reports` |
| `smoke.mjs` | Node smoke test of the built site (CI) |
| `build.sh` | Assembles `web/dist` |

Deployed to GitHub Pages by `.github/workflows/pages.yml` on pushes to `main`.
