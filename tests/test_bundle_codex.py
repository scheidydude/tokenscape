from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

import tokenscape.bundle as bundle_mod
from tokenscape.bundle import create, source_context
from tokenscape.cli import app
from tokenscape.codex_parser import stream_sessions, stream_turns

FIXTURES = Path(__file__).parent / 'fixtures'
CLAUDE = (FIXTURES / 'sample-session.jsonl').read_text()
CODEX = (FIXTURES / 'sample-codex-session.jsonl').read_text()


@pytest.fixture
def mixed_bundle(tmp_path: Path) -> Path:
    path = tmp_path / 'mixed.zip'
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('projects/p/a.jsonl', CLAUDE)
        zf.writestr('codex-sessions/2026/06/09/rollout-1.jsonl', CODEX)
    return path


@pytest.fixture
def local_sessions(tmp_path: Path, monkeypatch) -> Path:
    home = tmp_path / 'home'
    (home / 'claude' / 'p').mkdir(parents=True)
    (home / 'claude' / 'p' / 'a.jsonl').write_text(CLAUDE)
    (home / 'codex' / '2026' / '06' / '09').mkdir(parents=True)
    (home / 'codex' / '2026' / '06' / '09' / 'rollout-1.jsonl').write_text(CODEX)
    monkeypatch.setattr(bundle_mod, 'claude_projects_dir', lambda: home / 'claude')
    monkeypatch.setattr(bundle_mod, 'claude_desktop_sessions_dir', lambda: None)
    monkeypatch.setattr(bundle_mod, 'codex_sessions_dir', lambda: home / 'codex')
    return home


def test_create_codex_bundle(tmp_path: Path, local_sessions: Path):
    path, count, _ = create(tmp_path / 'out.zip', tool='codex')
    assert count == 1
    assert zipfile.ZipFile(path).namelist() == ['codex-sessions/2026/06/09/rollout-1.jsonl']


def test_create_claude_bundle_has_no_codex(tmp_path: Path, local_sessions: Path):
    path, count, _ = create(tmp_path / 'out.zip')
    assert count == 1
    assert zipfile.ZipFile(path).namelist() == ['projects/p/a.jsonl']


def test_codex_bundle_round_trip(tmp_path: Path, local_sessions: Path):
    path, _, _ = create(tmp_path / 'out.zip', tool='codex')
    with source_context(str(path), tool='codex') as files:
        turns = list(stream_turns(files=files))
        sessions = list(stream_sessions(files=files))
    assert len(turns) == 2
    assert len(sessions) == 1
    assert turns[0].project == 'mycodexproject'


def test_mixed_bundle_picks_folders_by_tool(mixed_bundle: Path):
    with source_context(str(mixed_bundle), tool='codex') as files:
        assert [f.name for f in files] == ['rollout-1.jsonl']
    with source_context(str(mixed_bundle), tool='claude') as files:
        assert [f.name for f in files] == ['a.jsonl']


def test_claude_bundle_has_nothing_for_codex(tmp_path: Path):
    path = tmp_path / 'claude.zip'
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('projects/p/a.jsonl', CLAUDE)
    with source_context(str(path), tool='codex') as files:
        assert files == []


def test_plain_zip_of_codex_sessions(tmp_path: Path):
    # e.g. `cd ~/.codex && zip -r x.zip sessions` — no bundle folders, so every .jsonl is read
    path = tmp_path / 'plain.zip'
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('sessions/2026/06/09/rollout-1.jsonl', CODEX)
    with source_context(str(path), tool='codex') as files:
        assert len(list(stream_turns(files=files))) == 2


def test_codex_directory_source(tmp_path: Path):
    (tmp_path / 'codex-sessions' / 'x').mkdir(parents=True)
    (tmp_path / 'codex-sessions' / 'x' / 'r.jsonl').write_text(CODEX)
    (tmp_path / 'projects').mkdir()
    (tmp_path / 'projects' / 'a.jsonl').write_text(CLAUDE)
    with source_context(str(tmp_path), tool='codex') as files:
        assert [f.name for f in files] == ['r.jsonl']


def test_unknown_tool_rejected(mixed_bundle: Path):
    with pytest.raises(ValueError, match='unknown tool'):
        with source_context(str(mixed_bundle), tool='gemini'):
            pass


def test_cli_codex_source_reads_the_bundle(mixed_bundle: Path, monkeypatch):
    # Before change 5 this silently read ~/.codex instead of the bundle.
    import tokenscape.codex_parser as codex_mod
    monkeypatch.setattr(codex_mod, 'codex_sessions_dir', lambda: None)
    result = CliRunner().invoke(app, [
        '--tool', 'codex', 'full-report', '--source', str(mixed_bundle),
        '--from', '2026-06-01', '--to', '2026-06-30',
    ])
    assert result.exit_code == 0, result.output
    assert 'mycodexproject' in result.output
    assert '— CODEX' in result.output


def test_cli_missing_source(tmp_path: Path):
    result = CliRunner().invoke(app, ['full-report', '--source', str(tmp_path / 'nope.zip')])
    assert result.exit_code == 1
    assert 'no such file' in result.output


def test_cli_codex_source_without_codex_sessions(tmp_path: Path):
    path = tmp_path / 'claude.zip'
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('projects/p/a.jsonl', CLAUDE)
    result = CliRunner().invoke(app, ['--tool', 'codex', 'full-report', '--source', str(path)])
    assert result.exit_code == 1
    assert 'no CODEX session files' in result.output
