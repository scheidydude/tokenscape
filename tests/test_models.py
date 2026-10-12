from __future__ import annotations

import pytest

from tokenscape.models import display_name


@pytest.mark.parametrize(('raw', 'name'), [
    ('claude-opus-5-5', 'Opus 5.5'),
    ('claude-opus-5', 'Opus 5'),
    ('claude-sonnet-5', 'Sonnet 5'),
    ('claude-sonnet-5-5', 'Sonnet 5.5'),
    ('claude-sonnet-4-6-20260101', 'Sonnet 4.6'),
    ('claude-opus-4-7', 'Opus 4.7'),
    ('some-unknown-model', 'some-unknown-model'),
])
def test_display_name(raw: str, name: str):
    assert display_name(raw) == name
