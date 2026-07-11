from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime, timedelta

from rich.console import Console

from .aggregate import aggregate_turns
from .parser import stream_turns

console = Console()


def _period_range(label: str) -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    if label == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif label == '7d':
        start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = (now - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def _agg_for(label: str) -> dict[str, object]:
    from_dt, to_dt = _period_range(label)
    result = aggregate_turns(stream_turns(from_dt=from_dt, to_dt=to_dt))
    u = result.totals.usage
    return {
        'period': label,
        'total': u.total,
        'input': u.input,
        'output': u.output,
        'cache_read': u.cache_read,
        'cache_write': u.cache_write,
        'turns': result.totals.turn_count,
    }


def run_export(fmt: str = 'csv') -> None:
    periods = [_agg_for(p) for p in ('today', '7d', '30d')]

    if fmt == 'json':
        sys.stdout.write(json.dumps(periods, indent=2) + '\n')
        return

    writer = csv.DictWriter(sys.stdout, fieldnames=list(periods[0].keys()))
    writer.writeheader()
    writer.writerows(periods)
