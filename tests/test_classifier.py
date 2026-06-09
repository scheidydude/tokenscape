from __future__ import annotations

from datetime import datetime, timezone

from hindsight.classifier import Activity, classify
from hindsight.types import TokenUsage, Turn


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


# ── Codex tool names ──────────────────────────────────────────────────────────

def test_codex_coding_apply_patch():
    assert classify(_turn(['apply_patch'])) == Activity.CODING


def test_codex_coding_write_file():
    assert classify(_turn(['write_file'])) == Activity.CODING


def test_codex_coding_patch_apply():
    assert classify(_turn(['patch_apply'])) == Activity.CODING


def test_codex_exploration_read_file():
    assert classify(_turn(['read_file'])) == Activity.EXPLORATION


def test_codex_exploration_search_files():
    assert classify(_turn(['search_files'])) == Activity.EXPLORATION


def test_codex_feature_dev():
    assert classify(_turn(['apply_patch'], 'add a readme file')) == Activity.FEATURE_DEV


def test_codex_refactoring():
    assert classify(_turn(['write_file'], 'refactor the auth module')) == Activity.REFACTORING


def test_codex_debugging():
    assert classify(_turn(['apply_patch'], 'fix this bug')) == Activity.DEBUGGING


def test_codex_mixed_edit_and_explore():
    # edit tool present → Coding, not Exploration
    assert classify(_turn(['read_file', 'apply_patch'])) == Activity.CODING
