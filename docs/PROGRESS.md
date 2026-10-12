# Progress: tokenscape web service

## Session 2026-10-11
- Investigated whether tokenscape could run as a web service taking an uploaded sessions zip
- Wrote design doc (Claude Docs + `docs/web-service-design.md`); committed `af3cbab`, pushed
- Added non-goal: no CLI install changes; committed `0994ee7`
- Blocked: push of `0994ee7` failed — SSH agent signing error; user to unlock agent and push

## Session 2026-10-12
- Created `docs/PLAN.md`, `docs/PROGRESS.md`, `docs/FINDINGS.md` from the design doc
- Next: Phase 0, change 1 (explicit file lists in parser)
- Push of `0994ee7` resolved; went up with `4a21501`
- Phase 0 started
  - Baseline: real 32-file bundle (32MB) → `full-report` md+html deterministic; local report baseline too
  - Change 1: `stream_turns`/`stream_sessions`/`list_projects` take `files=`; `source_context` now yields a file list; monkeypatch removed
  - Change 2: `ZipLimits` + `UnsafeBundleError` in `bundle.py`; zip read in place via `zipfile.Path`; CLI prints error, exits 1
  - Before/after: zip, directory and local reports identical except "Generated" timestamp
  - Added `tests/test_bundle.py` (14 tests incl. parallel bundles with barrier); 76/76 pass, ruff clean
- Committed and pushed Phase 0; user deferred version bump and PyPI release
- Next: Phase 1 spike (Pyodide), or release when user says go
- Phase 1 started
  - CI green on `2be3200`
  - Spike (scratchpad, Node 22 + `pyodide@0.28.3`): copied `src/tokenscape/*.py` into Pyodide FS, ran `source_context` → parser → `report.generate` + `html_report.generate` on the real bundle
  - Output identical to native CLI (md + html, minus "Generated" line) once dates matched
  - Perf: 13MB zip 1.3s total; 57MB zip 2.6s; 226MB zip (509MB raw) 7.6s, ~450MB RSS; native CLI 3.75s on the 226MB zip
  - Fixed `\-` invalid escape in `html_report.py` JS regex (warned on Python 3.13/Pyodide); HTML output byte-identical
  - Added `tests/test_core_imports.py`; 77/77 pass, ruff clean
- Next: user to confirm site location (`web/` in repo vs separate repo) and hosting (GitHub Pages); then drop-zone page
  - User chose `web/` in this repo + GitHub Pages
  - Added `src/tokenscape/webapp.py` (`build_reports` → JSON; inclusive UTC dates; errors returned, not raised) + `tests/test_webapp.py`
  - Built `web/`: page, worker (Pyodide self-hosted, wheel via `unpackArchive`), `build.sh`, `smoke.mjs`, README
  - Fixes during build: `uv build` leaves a `.gitignore` in its out dir (rm -rf); `"type": "module"` broke Pyodide's CJS file under Node (removed); Pyodide rejects Node `Buffer` (wrap in `Uint8Array`)
  - Headless Chrome (system Chrome via playwright-core, scratchpad): real bundle 1,404 turns in 0.8s; charts render; unsafe zip → friendly error; custom range + last-7-days correct; 400px layout ok; no requests during analysis
  - Fixed: custom date fields visible when hidden (`.row` flex beat `[hidden]`); favicon 404
  - Screenshots in `screenshots/` (gitignored)
  - Added `.github/workflows/pages.yml` and a `web` job in `ci.yml`; 81/81 tests pass, ruff clean
- Next: commit + push; user to enable Pages (Source: GitHub Actions); confirm deploy; README link
- Enabled GitHub Pages (build_type=workflow) via `gh api`; pushed `8d58e3f`
- Pages run: build + smoke + deploy green; CI green on 3.11/3.12/3.13 + web job
- Live site e2e (headless Chrome): real bundle 0.6s, charts render, unsafe zip rejected, only host scheidydude.github.io, no requests during analysis, no console errors; `.wasm` served as `application/wasm`
- Linked site from README; Phase 1 complete
- Open: PyPI release of Phase 0/1 core changes still deferred by user
- Fixed model display names: `claude-sonnet-5` → Sonnet 5, `claude-opus-5-5` → Opus 5.5 (+ Opus 5 / Sonnet 5.5 so they don't mislabel); `tests/test_models.py`; 88/88 pass
