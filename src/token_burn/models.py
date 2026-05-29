import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r'claude-opus-4-7'), 'Opus 4.7'),
    (re.compile(r'claude-opus-4-6'), 'Opus 4.6'),
    (re.compile(r'claude-opus-4-5'), 'Opus 4.5'),
    (re.compile(r'claude-opus-4'), 'Opus 4'),
    (re.compile(r'claude-sonnet-4-6'), 'Sonnet 4.6'),
    (re.compile(r'claude-sonnet-4-5'), 'Sonnet 4.5'),
    (re.compile(r'claude-sonnet-4'), 'Sonnet 4'),
    (re.compile(r'claude-haiku-4-5'), 'Haiku 4.5'),
    (re.compile(r'claude-haiku-4'), 'Haiku 4'),
    (re.compile(r'claude-3-5-sonnet'), 'Sonnet 3.5'),
    (re.compile(r'claude-3-5-haiku'), 'Haiku 3.5'),
    (re.compile(r'claude-3-opus'), 'Opus 3'),
    (re.compile(r'claude-3-sonnet'), 'Sonnet 3'),
    (re.compile(r'claude-3-haiku'), 'Haiku 3'),
]


def display_name(model: str) -> str:
    for pattern, name in _PATTERNS:
        if pattern.search(model):
            return name
    return model
