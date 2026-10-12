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
