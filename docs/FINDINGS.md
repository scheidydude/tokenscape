# Findings: tokenscape web service

## Existing code relevant to a web version
- `full-report --source <zip> --html-output` already does the whole pipeline from a zip; `html_report.py` output is self-contained
- `bundle.py:source_context` swaps out the module-level `parser_mod._iter_session_files` → not safe when two requests run at once
- `bundle.py` uses `zipfile.extractall` with no limits → zip bomb / path risk on untrusted input
- `semantic.py:16-18` caches embeddings/labels/summaries in `~/.cache/tokenscape` → would be shared across users on a server
- `--summarize` reads LLM config from `~/.config/tokenscape/config.toml` (`cli.py:706-711`)
- `bundle` and `--source` handle Claude sessions only; Codex not covered
- Core runtime deps: `typer`, `textual`, `rich`; analysis core needs only stdlib + `rich` (to verify in Phase 1 spike)
- `Turn` (`types.py`) keeps `user_text`, `bash_inputs`, `edited_files`, `cwd` — sensitive even after parsing

## Decisions
- Browser-only (Pyodide) first: data never leaves the user's machine; static hosting; no compliance burden
- Metrics-only hosted service only if team views are wanted; full upload is a last resort
- Web pieces never change the default CLI install: static site separate; any server deps go in an optional extra or separate package
- Semantic clustering not offered in browser (fastembed needs onnxruntime + 130MB model)
- Plan files live in `docs/` (user preference), not repo root

## Phase 0
- Real `.jsonl` transcripts compress ~5x (max 5.3x in a 32-file bundle) → per-entry ratio limit 200x has wide margin; only applied to entries > 1MiB
- `zipfile.ZipExtFile` caps output at the declared `file_size` (CRC checked), so checking declared sizes up front is enough against zip bombs
- `zipfile.Path.open(encoding=..., errors=...)` works in text mode on 3.11 → parser reads zip entries without extraction, no code changes in `_stream_jsonl`
- Since nothing is extracted, path checks are defense-in-depth (and catch malformed bundles), not the main protection
- Decision: non-`.jsonl` entries are ignored rather than rejected (Finder/`__MACOSX` junk is common in hand-made zips)
- Decision: default limits are generous for CLI (100k files, 20GiB); a web service passes tighter `ZipLimits`
- Known gap (change 5): `--tool codex --source X` silently reads `~/.codex`, ignoring the bundle — same as before Phase 0
- Full report is deterministic apart from the "Generated" timestamp line → before/after diff with `grep -v Generated`

## Phase 1 spike
- Core modules (parser, bundle, aggregate, patterns, classifier, report, html_report) import only stdlib → no `rich` needed in browser; `typer`/`textual` never loaded
- Pyodide 0.28.3 = Python 3.13; `tokenscape` targets >=3.11, no 3.13 incompatibilities found
- Semantic clusters skip cleanly in Pyodide: `report.py`/`html_report.py` catch `ModuleNotFoundError` (numpy/fastembed not loaded)
- `source_context` + `zipfile.Path` work unchanged on Pyodide's in-memory FS
- Pipeline glue for the page (mirrors `cli.full_report._run`): `source_context(zip)` → `stream_turns(files=)` + `stream_sessions(files=)` → `aggregate_turns` → `report.generate(**kw)` / `html_report.generate(**kw)`
- CLI quirk (pre-existing): `--to YYYY-MM-DD` means midnight at the start of that day, so the day itself is excluded; the page should define its own date handling
- Pyodide ~2x slower than native; memory ~450MB for a 509MB-raw bundle → fine for desktop browsers, worth a warning above ~250MB zips
- Packaging: page can install a wheel built from the repo via `micropip.install(url, deps=False)`; no PyPI release needed
- Python 3.12+ warns on invalid escapes in normal strings; 3.11 (our dev venv) is silent → `python -W error` compile check catches them

## Phase 1 build
- Meta-tag CSP doesn't apply to Web Workers (they take policy from their own response headers) → self-host Pyodide so the worker only runs our own code
- `srcdoc` iframes inherit the parent CSP → report needs `'unsafe-inline'` + cdnjs (Chart.js) in `script-src`; `connect-src 'self'` still blocks exfiltration from the report frame
- Report iframe is `sandbox="allow-scripts"` (no same-origin) → can't touch the page or worker
- `pyodide.unpackArchive(bytes, 'wheel')` installs the wheel incl. `.dist-info` → `importlib.metadata.version` works; no micropip/network
- Pyodide in Node: don't set `"type": "module"` next to copied `pyodide.asm.js` (CommonJS); pass `Uint8Array`, not `Buffer`
- Playwright doesn't report requests from the opaque-origin report iframe; verified Chart.js via rendered charts instead
- Fixed 2026-10-12: `models.display_name` now maps `claude-sonnet-5` / `claude-opus-5-5` (were shown raw)
- Site size ~12MB (Pyodide wasm 8.6MB + stdlib 2.4MB); first load cached by browser after

## Change 5 (Codex bundles)
- Decision: bundle contents follow `--tool` rather than always including both tools — a plain `bundle` never starts including Codex transcripts the user didn't intend to share
- Folder per tool in the zip (`BUNDLE_DIRS` in `bundle.py`); any known folder present → only the chosen tool's folders are read, so a Claude bundle gives Codex zero files (clear error) instead of misparsing
- Fixed 2026-10-12: Codex model came from the instructions text ("based on GPT-6." → `gpt-6.`; GPT-5.5 sessions showed as GPT-5). Every real session has `turn_context.payload.model` → now used per turn; text regex is only a fallback and stops before a trailing '.'
