from __future__ import annotations

from datetime import datetime, timezone

from hindsight.patterns import (
    GrowthSignal,
    _normalize_cmd,
    activity_transitions,
    file_edit_frequency,
    growth_signals,
    model_activity_breakdown,
    model_efficiency_signals,
    session_ramp_stats,
    shell_automation_candidates,
)
from hindsight.types import TokenUsage, Turn

_TS = datetime(2026, 1, 1, tzinfo=timezone.utc)
_USAGE = TokenUsage(input=100, output=50, cache_read=0, cache_write=0)


def _turn(tools: list[str] = (), bash: list[str] = (), edited: list[str] = (), text: str = '', project: str = 'proj') -> Turn:
    return Turn(
        message_id='x',
        timestamp=_TS,
        model='Sonnet 4.6',
        usage=_USAGE,
        tools_used=list(tools),
        bash_inputs=list(bash),
        edited_files=list(edited),
        user_text=text,
        project=project,
    )


def test_normalize_cmd_two_words():
    assert _normalize_cmd('git add src/foo.py') == 'git add'


def test_normalize_cmd_single_word():
    assert _normalize_cmd('pytest') == 'pytest'


def test_normalize_cmd_empty():
    assert _normalize_cmd('') == ''


def test_normalize_cmd_strips_flags():
    assert _normalize_cmd('docker compose up -d') == 'docker compose'


def test_shell_candidates_min_count():
    turns = [_turn(bash=['git add src/foo.py']) for _ in range(5)]
    turns += [_turn(bash=['pytest tests/']) for _ in range(2)]
    result = shell_automation_candidates(turns, min_count=3)
    commands = [r.command for r in result]
    assert 'git add' in commands
    assert 'pytest tests/' not in commands


def test_shell_candidates_normalization():
    turns = [_turn(bash=['git add src/a.py']), _turn(bash=['git add src/b.py']), _turn(bash=['git add tests/c.py'])]
    result = shell_automation_candidates(turns, min_count=3)
    assert len(result) == 1
    assert result[0].command == 'git add'
    assert result[0].count == 3


def test_shell_candidates_examples():
    turns = [
        _turn(bash=['git add src/a.py']),
        _turn(bash=['git add src/b.py']),
        _turn(bash=['git add src/c.py']),
    ]
    result = shell_automation_candidates(turns, min_count=3)
    assert len(result[0].examples) <= 3


def test_file_edit_frequency():
    turns = [
        _turn(edited=['src/foo.py', 'src/bar.py']),
        _turn(edited=['src/foo.py']),
        _turn(edited=['src/baz.py']),
    ]
    result = file_edit_frequency(turns)
    assert result[0] == ('src/foo.py', 2)
    assert len(result) == 3


def test_activity_transitions():
    from hindsight.classifier import Activity
    # Two sessions: Exploration → Coding, Exploration → Coding
    t_explore = _turn(tools=['Read'])
    t_code = _turn(tools=['Edit'], text='add feature')
    sessions = [[t_explore, t_code], [t_explore, t_code]]
    transitions = activity_transitions(sessions)
    assert len(transitions) > 0
    top = transitions[0]
    assert top.count == 2
    assert top.pct == 1.0


def test_session_ramp_no_edit():
    sessions = [[_turn(tools=['Read']), _turn(tools=['Read'])]]
    ramp = session_ramp_stats(sessions)
    assert ramp.mean == 0.0
    assert ramp.p90 == 0.0
    assert ramp.session_count == 1


def test_session_ramp_first_turn_edit():
    sessions = [[_turn(tools=['Edit'])]]
    ramp = session_ramp_stats(sessions)
    assert ramp.mean == 0.0


def test_session_ramp_third_turn():
    sessions = [[_turn(), _turn(), _turn(tools=['Edit'])]]
    ramp = session_ramp_stats(sessions)
    assert ramp.mean == 2.0


def test_growth_signals_no_tests():
    turns = [_turn(tools=['Edit'], text='fix bug error') for _ in range(6)]
    signals = growth_signals(turns)
    kinds = [s.kind for s in signals]
    assert 'no_tests' in kinds


def test_growth_signals_high_conversation():
    # 8/10 turns = 80% conversation, well above 40% threshold
    turns = [_turn() for _ in range(8)] + [_turn(tools=['Edit']) for _ in range(2)]
    signals = growth_signals(turns)
    kinds = [s.kind for s in signals]
    assert 'high_conversation' in kinds


def test_growth_signals_clean_project():
    # Balanced debug/test ratio, low conversation
    debug_turns = [_turn(tools=['Edit'], text='fix bug error') for _ in range(3)]
    test_turns = [_turn(bash=['pytest tests/']) for _ in range(3)]
    code_turns = [_turn(tools=['Edit']) for _ in range(4)]
    signals = growth_signals(debug_turns + test_turns + code_turns)
    assert not any(s.kind == 'no_tests' for s in signals)


def _turn_model(model: str, tools: list[str] = (), bash: list[str] = ()) -> Turn:
    return Turn(
        message_id='x',
        timestamp=_TS,
        model=model,
        usage=_USAGE,
        tools_used=list(tools),
        bash_inputs=list(bash),
        edited_files=[],
        user_text='',
        project='proj',
        cwd='/proj',
    )


def test_model_activity_breakdown_groups_by_model():
    turns = (
        [_turn_model('Sonnet 4.6', tools=['Edit'])] * 4
        + [_turn_model('Opus 4.7')] * 2
    )
    stats = model_activity_breakdown(turns)
    models = [s.model for s in stats]
    assert 'Sonnet 4.6' in models
    assert 'Opus 4.7' in models


def test_model_activity_breakdown_sorted_by_tokens():
    turns = (
        [_turn_model('Sonnet 4.6', tools=['Edit'])] * 6
        + [_turn_model('Haiku 4.5')] * 2
    )
    stats = model_activity_breakdown(turns)
    assert stats[0].model == 'Sonnet 4.6'


def test_model_efficiency_signals_flags_cheap_overhead():
    # 8 conversation turns (no tools) + 2 coding turns = 80% cheap
    turns = [_turn_model('Opus 4.7')] * 8 + [_turn_model('Opus 4.7', tools=['Edit'])] * 2
    stats = model_activity_breakdown(turns)
    signals = model_efficiency_signals(stats)
    assert any(sig.model == 'Opus 4.7' for sig in signals)


def test_model_efficiency_signals_no_flag_for_coding_heavy():
    # All coding turns — should not be flagged
    turns = [_turn_model('Sonnet 4.6', tools=['Edit'])] * 10
    stats = model_activity_breakdown(turns)
    signals = model_efficiency_signals(stats)
    assert not signals
