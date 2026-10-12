# Plan: tokenscape web service

Source: [web-service-design.md](web-service-design.md)

## Goal
Let users get the tokenscape HTML report from a sessions zip without installing Python, starting with a browser-only app (no data leaves the machine). The CLI install stays unchanged: no new dependencies or behavior changes.

## Phases
- [ ] Phase 0: CLI prerequisites (ships as a normal PyPI release)
  - [x] Change 1: pass session file lists explicitly into `stream_turns` / `stream_sessions`; remove the `_iter_session_files` monkeypatch in `bundle.py:source_context`
  - [x] Change 2: harden zip reading — caps on uncompressed size, file count and compression ratio; non-`.jsonl` entries ignored; reject absolute/`..`/drive paths; read entries from the zip instead of `extractall`
  - [x] Tests: two bundles parsed in parallel give correct, separate results
  - [x] Tests: malicious zips (zip bomb, `../` path, size/count limits, invalid zip) are rejected; non-jsonl entries ignored
  - [x] Confirm CLI output unchanged on an existing bundle (before/after diff of `full-report`)
  - [ ] ruff + pytest green; bump version, tag, release
- [ ] Phase 1: browser-only app (Option A)
  - [x] Spike: load the core in Pyodide — works unchanged under Node + Pyodide 0.28.3; no blockers (core is pure stdlib, not even `rich`)
  - [x] Split a core import path that doesn't pull in CLI/TUI modules — already true; guarded by `tests/test_core_imports.py`
  - [x] Drop-zone page: read zip in browser → run analysis → render `html_report` output (`web/`; Pyodide in a Web Worker; entry point `tokenscape.webapp.build_reports`)
  - [x] Semantic clustering disabled in browser; degrade gracefully (existing `ModuleNotFoundError` path)
  - [x] Perf test: 226MB zip / 509MB raw → 7.6s total, ~450MB RSS in Node (native: 3.75s)
  - [x] Verify zero network requests after page load (headless Chrome: none during analysis; CSP `connect-src 'self'`; Pyodide self-hosted)
  - [x] Build: wheel from repo served by the site, installed with `pyodide.unpackArchive` — no PyPI release or micropip needed
  - [x] Node smoke test (`web/smoke.mjs`) in CI (`ci.yml` web job) and before each Pages deploy
  - [x] Decide location and hosting: `web/` in this repo, GitHub Pages (user, 2026-10-12)
  - [ ] Enable Pages (Settings → Pages → Source: GitHub Actions), push, confirm deploy
  - [ ] Link the live site from README
- [ ] Phase 2: metrics-only bundles (Option B) — only if team views are wanted
  - [ ] Define versioned metrics-only format (timestamp, model, token counts, tool names, hashed project)
  - [ ] `bundle --metrics-only` CLI flag (optional; default `bundle` unchanged)
  - [ ] Server API accepting only that format, in an optional `tokenscape[web]` extra or separate package
  - [ ] Change 3: per-run/configurable caches (`semantic.py:16-18`)
  - [ ] Security checklist items for B (design doc) satisfied
- [ ] Phase 3: full upload (Option C) — only with a clear need
  - [ ] Change 4: per-request LLM provider config (`cli.py:706-711`, `report.py:203`)
  - [ ] Secret scrubbing before any LLM call
  - [ ] Full security checklist + security review before launch
- [ ] Parallel / anytime: Change 5 — Codex support in `bundle` and `--source`

## Status
Phase 0 done except release (deferred by user). Phase 1 built and tested locally; next: enable GitHub Pages, deploy, link from README.
