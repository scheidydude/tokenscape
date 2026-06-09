from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tokenscape.parser import _is_injected_content, _parse_iso, _project_name, _stream_jsonl


def test_parse_iso_utc():
    dt = _parse_iso('2026-05-29T10:00:00Z')
    assert dt.tzinfo is not None
    assert dt.year == 2026


def test_parse_iso_offset():
    dt = _parse_iso('2026-05-29T10:00:00+00:00')
    assert dt.year == 2026


def test_project_name():
    assert _project_name('/Users/david/myproject') == 'myproject'
    assert _project_name('') == 'unknown'


def test_stream_jsonl_dedup(tmp_path: Path):
    fixture = Path(__file__).parent / 'fixtures' / 'sample-session.jsonl'
    entries = list(_stream_jsonl(fixture))
    assert len(entries) == 5


def test_stream_turns_dedup(tmp_path: Path, monkeypatch):
    fixture = Path(__file__).parent / 'fixtures' / 'sample-session.jsonl'

    import tokenscape.parser as parser_mod

    def mock_iter():
        yield fixture

    monkeypatch.setattr(parser_mod, '_iter_session_files', mock_iter)

    from tokenscape.parser import stream_turns
    turns = list(stream_turns())
    ids = [t.message_id for t in turns]
    # msg_01 appears twice in fixture but should only be counted once
    assert ids.count('msg_01') == 1
    assert len(turns) == 2


def test_is_injected_content_skill_body():
    assert _is_injected_content('Base directory for this skill: /foo')
    assert not _is_injected_content('Let me fix that bug.')


def test_is_injected_content_xml():
    assert _is_injected_content('<task-notification>foo</task-notification>')
    assert not _is_injected_content('Show me the task list.')


def test_is_injected_content_shell_prompt():
    assert _is_injected_content('(base) david@Mac orchid % which codeindex\n/opt/homebrew/bin/codeindex')
    assert _is_injected_content('$ git status\nOn branch main')
    assert _is_injected_content('% ls -la\ntotal 42')
    assert not _is_injected_content('What does this function do?')
    assert not _is_injected_content('(some parenthetical note without a trailing space-word)')


def test_stream_turns_token_values(monkeypatch):
    fixture = Path(__file__).parent / 'fixtures' / 'sample-session.jsonl'

    import tokenscape.parser as parser_mod

    def mock_iter():
        yield fixture

    monkeypatch.setattr(parser_mod, '_iter_session_files', mock_iter)

    from tokenscape.parser import stream_turns
    turns = {t.message_id: t for t in stream_turns()}
    t1 = turns['msg_01']
    assert t1.usage.input == 1000
    assert t1.usage.output == 200
    assert t1.usage.cache_read == 500
    assert t1.usage.cache_write == 100
    assert t1.usage.total == 1800
    assert t1.model == 'Sonnet 4.6'
    assert t1.project == 'myproject'
