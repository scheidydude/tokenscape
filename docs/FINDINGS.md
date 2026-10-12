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
