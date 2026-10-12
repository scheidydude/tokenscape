'''Entry point for the browser build (Pyodide): a bundle zip in, markdown + HTML reports out.

Stdlib-only on purpose: the page loads just the core modules, never the CLI/TUI dependencies.
'''
from __future__ import annotations

import json
from datetime import UTC, datetime, time, timedelta
from importlib.metadata import PackageNotFoundError, version

from .aggregate import aggregate_turns
from .bundle import UnsafeBundleError, source_context
from .html_report import generate as generate_html
from .parser import stream_sessions, stream_turns
from .report import generate as generate_md


def _version() -> str:
    try:
        return version('tokenscape')
    except PackageNotFoundError:
        return 'dev'


def _day_start(date: str) -> datetime:
    return datetime.combine(datetime.fromisoformat(date).date(), time.min, tzinfo=UTC)


def build_reports(
    zip_path: str,
    from_date: str | None = None,
    to_date: str | None = None,
    period_label: str = 'all time',
    top: int = 8,
) -> str:
    '''Analyze the bundle at `zip_path` and return a JSON string for the page.

    `from_date` / `to_date` are inclusive YYYY-MM-DD days in UTC; either may be omitted.
    The result has either an `error` key or `markdown`, `html` and summary counts.
    '''
    from_dt = _day_start(from_date) if from_date else None
    to_dt = _day_start(to_date) + timedelta(days=1) - timedelta(microseconds=1) if to_date else None

    try:
        with source_context(zip_path) as files:
            if not files:
                return json.dumps({'error': 'No .jsonl session files found in this zip.'})
            turns = list(stream_turns(from_dt=from_dt, to_dt=to_dt, files=files))
            sessions = list(stream_sessions(from_dt=from_dt, to_dt=to_dt, files=files))
    except UnsafeBundleError as exc:
        return json.dumps({'error': f'This zip was rejected: {exc}'})

    if not turns:
        return json.dumps({'error': 'No sessions with token usage in the selected period.', 'files': len(files)})

    # Open-ended ranges show the span of the data itself in the report header.
    from_dt = from_dt or min(t.timestamp for t in turns)
    to_dt = to_dt or max(t.timestamp for t in turns)
    kwargs = dict(
        turns=turns,
        sessions=sessions,
        result=aggregate_turns(iter(turns)),
        from_dt=from_dt,
        to_dt=to_dt,
        period_label=period_label,
        top=top,
        labels_config=None,
        summarize_config=None,
        force_summary=False,
        tool_label='CLAUDE',
    )
    return json.dumps({
        'markdown': generate_md(**kwargs),
        'html': generate_html(**kwargs),
        'files': len(files),
        'turns': len(turns),
        'sessions': len(sessions),
        'from': str(from_dt.date()),
        'to': str(to_dt.date()),
        'version': _version(),
    })
