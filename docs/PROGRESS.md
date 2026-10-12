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
