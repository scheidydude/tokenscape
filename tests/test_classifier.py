from __future__ import annotations

from datetime import datetime, timezone

from token_burn.classifier import Activity, classify
from token_burn.types import TokenUsage, Turn


def _turn(tools: list[str], text: str = '') -> Turn:
    return Turn(
        message_id='x',
        timestamp=datetime.now(timezone.utc),
        model='Sonnet 4.6',
        usage=TokenUsage(100, 50, 0, 0),
        tools_used=tools,
        user_text=text,
    )


def test_coding():
    assert classify(_turn(['Edit'])) == Activity.CODING


def test_exploration():
    assert classify(_turn(['Read', 'Grep'])) == Activity.EXPLORATION


def test_conversation():
    assert classify(_turn([])) == Activity.CONVERSATION


def test_delegation():
    assert classify(_turn(['Agent'])) == Activity.DELEGATION


def test_planning():
    assert classify(_turn(['EnterPlanMode'])) == Activity.PLANNING


def test_feature_dev():
    assert classify(_turn(['Edit'], 'add a login button')) == Activity.FEATURE_DEV


def test_refactoring():
    assert classify(_turn(['Edit'], 'refactor the auth module')) == Activity.REFACTORING


def test_debugging():
    assert classify(_turn(['Edit'], 'fix this bug')) == Activity.DEBUGGING
