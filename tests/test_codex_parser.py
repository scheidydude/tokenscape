from __future__ import annotations

from datetime import UTC
from pathlib import Path

from tokenscape.codex_parser import _project_name, _stream_jsonl, _stream_turns_from_path

FIXTURE = Path(__file__).parent / 'fixtures' / 'sample-codex-session.jsonl'


def test_project_name():
    assert _project_name('/Users/david/mycodexproject') == 'mycodexproject'
    assert _project_name('') == 'unknown'


def test_stream_jsonl_count():
    entries = list(_stream_jsonl(FIXTURE))
    assert len(entries) == 15


def test_stream_turns_count():
    turns = list(_stream_turns_from_path(FIXTURE, set()))
    assert len(turns) == 2


def test_turn_deduplication():
    seen: set[str] = set()
    turns = list(_stream_turns_from_path(FIXTURE, seen))
    assert len(turns) == 2
    # second call with same seen_ids yields nothing
    turns2 = list(_stream_turns_from_path(FIXTURE, seen))
    assert len(turns2) == 0


def test_turn_token_accumulation():
    turns = {t.message_id: t for t in _stream_turns_from_path(FIXTURE, set())}
    t1 = turns['turn-01']
    # two token_count events: last_token_usage sums
    assert t1.usage.input == 1000 + 1000
    assert t1.usage.output == 100 + 200
    assert t1.usage.cache_read == 400 + 500
    assert t1.usage.cache_write == 0
    assert t1.usage.total == 2000 + 300 + 900


def test_turn_model_extracted():
    turns = list(_stream_turns_from_path(FIXTURE, set()))
    assert turns[0].model == 'GPT-5'


def test_turn_project_and_cwd():
    turns = list(_stream_turns_from_path(FIXTURE, set()))
    assert turns[0].project == 'mycodexproject'
    assert turns[0].cwd == '/Users/david/mycodexproject'


def test_turn_user_text():
    turns = {t.message_id: t for t in _stream_turns_from_path(FIXTURE, set())}
    assert turns['turn-01'].user_text == 'add a readme file'
    assert turns['turn-02'].user_text == 'what does this function do'


def test_turn_tools_used():
    turns = {t.message_id: t for t in _stream_turns_from_path(FIXTURE, set())}
    t1 = turns['turn-01']
    assert 'exec_command' in t1.tools_used
    assert 'apply_patch' in t1.tools_used
    t2 = turns['turn-02']
    assert 'read_file' in t2.tools_used


def test_turn_bash_inputs():
    turns = {t.message_id: t for t in _stream_turns_from_path(FIXTURE, set())}
    assert turns['turn-01'].bash_inputs == ['ls -la']
    assert turns['turn-02'].bash_inputs == []


def test_turn_timestamp():
    turns = {t.message_id: t for t in _stream_turns_from_path(FIXTURE, set())}
    ts = turns['turn-01'].timestamp
    assert ts.year == 2026
    assert ts.month == 6
    assert ts.day == 9


def test_date_filter_excludes_old():
    from datetime import datetime
    cutoff = datetime(2026, 6, 9, 10, 0, 30, tzinfo=UTC)
    turns = list(_stream_turns_from_path(FIXTURE, set(), from_dt=cutoff))
    # turn-01 starts at 10:00:01, turn-02 at 10:01:00 — only turn-02 passes
    assert len(turns) == 1
    assert turns[0].message_id == 'turn-02'


def test_date_filter_excludes_future():
    from datetime import datetime
    cutoff = datetime(2026, 6, 9, 10, 0, 30, tzinfo=UTC)
    turns = list(_stream_turns_from_path(FIXTURE, set(), to_dt=cutoff))
    assert len(turns) == 1
    assert turns[0].message_id == 'turn-01'


def test_stream_turns_and_sessions(monkeypatch):
    import tokenscape.codex_parser as codex_mod

    def mock_iter():
        yield FIXTURE

    monkeypatch.setattr(codex_mod, '_iter_codex_session_files', mock_iter)

    from tokenscape.codex_parser import stream_sessions, stream_turns
    turns = list(stream_turns())
    assert len(turns) == 2

    sessions = list(stream_sessions())
    assert len(sessions) == 1
    assert len(sessions[0]) == 2
