# Plan: tokenscape web service

Source: [web-service-design.md](web-service-design.md)

## Goal
Let users get the tokenscape HTML report from a sessions zip without installing Python, starting with a browser-only app (no data leaves the machine). The CLI install stays unchanged: no new dependencies or behavior changes.

## Phases
- [ ] Phase 0: CLI prerequisites (ships as a normal PyPI release)
  - [ ] Change 1: pass session file lists explicitly into `stream_turns` / `stream_sessions`; remove the `_iter_session_files` monkeypatch in `bundle.py:source_context`
  - [ ] Change 2: harden zip reading — caps on uncompressed size, file count and compression ratio; `.jsonl` only; reject absolute/`..` paths; read entries from the zip instead of `extractall`
  - [ ] Tests: two bundles parsed in parallel give correct, separate results
  - [ ] Tests: malicious zips (zip bomb, `../` path, non-jsonl entries) are rejected
  - [ ] Confirm CLI output unchanged on an existing bundle (before/after diff of `full-report`)
  - [ ] ruff + pytest green; bump version, tag, release
- [ ] Phase 1: browser-only app (Option A)
  - [ ] Spike: load the core in Pyodide (stdlib + `rich`, no `typer`/`textual`); list import blockers
  - [ ] Split a core import path that doesn't pull in CLI/TUI modules
  - [ ] Drop-zone page: read zip in browser → run analysis → render `html_report` output
  - [ ] Semantic clustering disabled in browser; degrade gracefully
  - [ ] Perf test: 100MB bundle — parse time and memory
  - [ ] Verify zero network requests after page load
  - [ ] Decide location (`web/` folder vs separate repo) and hosting (GitHub Pages / static CDN)
  - [ ] Deploy static site; link from README
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
Not started. Next: Phase 0, change 1.
