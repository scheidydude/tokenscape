from __future__ import annotations

from datetime import datetime, timezone

from hindsight.aggregate import aggregate_turns
from hindsight.types import TokenUsage, Turn


def _turn(mid: str, project: str, model: str, tools: list[str], usage: TokenUsage) -> Turn:
    return Turn(
        message_id=mid,
        timestamp=datetime.now(timezone.utc),
        model=model,
        usage=usage,
        tools_used=tools,
        project=project,
    )


def test_aggregate_totals():
    turns = [
        _turn('1', 'proj-a', 'Sonnet 4.6', ['Edit'], TokenUsage(100, 50, 10, 5)),
        _turn('2', 'proj-b', 'Opus 4.7', ['Read'], TokenUsage(200, 80, 20, 0)),
    ]
    result = aggregate_turns(turns)
    assert result.totals.usage.total == 465
    assert result.totals.turn_count == 2


def test_aggregate_by_project():
    turns = [
        _turn('1', 'proj-a', 'Sonnet 4.6', [], TokenUsage(100, 0, 0, 0)),
        _turn('2', 'proj-a', 'Sonnet 4.6', [], TokenUsage(50, 0, 0, 0)),
        _turn('3', 'proj-b', 'Sonnet 4.6', [], TokenUsage(200, 0, 0, 0)),
    ]
    result = aggregate_turns(turns)
    assert result.by_project['proj-a'].usage.input == 150
    assert result.by_project['proj-b'].usage.input == 200


def test_aggregate_mcp_server():
    turns = [
        _turn('1', 'p', 'Sonnet', ['mcp__gmail__send'], TokenUsage(100, 50, 0, 0)),
    ]
    result = aggregate_turns(turns)
    assert 'gmail' in result.by_mcp_server
    assert result.by_mcp_server['gmail'].usage.total == 150
