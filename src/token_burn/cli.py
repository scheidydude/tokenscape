from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .aggregate import AggregateResult, aggregate_turns
from .parser import stream_turns
from .types import Aggregate, TokenUsage

app = typer.Typer(no_args_is_help=False, invoke_without_command=True)
console = Console()


def _today_range() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def _days_range(n: int) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=n - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def _month_range() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, now


def _usage_row(label: str, usage: TokenUsage) -> tuple[str, str, str, str, str, str]:
    return (label, str(usage.input), str(usage.output), str(usage.cache_read), str(usage.cache_write), str(usage.total))


def _print_agg_table(title: str, data: dict[str, Aggregate], sort_by_total: bool = True) -> None:
    table = Table(title=title, show_header=True, header_style='bold')
    table.add_column('Name')
    table.add_column('Input', justify='right')
    table.add_column('Output', justify='right')
    table.add_column('Cache Read', justify='right')
    table.add_column('Cache Write', justify='right')
    table.add_column('Total', justify='right')

    items = list(data.items())
    if sort_by_total:
        items.sort(key=lambda x: x[1].usage.total, reverse=True)

    for name, agg in items:
        table.add_row(*_usage_row(name, agg.usage))

    console.print(table)


def _run_report(from_dt: datetime, to_dt: datetime) -> AggregateResult:
    turns = stream_turns(from_dt=from_dt, to_dt=to_dt)
    return aggregate_turns(turns)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _launch_tui()


def _launch_tui() -> None:
    try:
        from .dashboard import TokenBurnApp
        TokenBurnApp().run()
    except ImportError:
        console.print('[yellow]TUI not available. Use subcommands: today, report, status, export[/yellow]')


@app.command()
def today() -> None:
    '''Show today\'s token usage.'''
    from_dt, to_dt = _today_range()
    result = _run_report(from_dt, to_dt)

    console.print(f'\n[bold]Today ({from_dt.strftime("%Y-%m-%d")})[/bold]\n')
    console.print(f'Total tokens: [bold]{result.totals.usage.total:,}[/bold]')
    console.print(f'  Input:       {result.totals.usage.input:,}')
    console.print(f'  Output:      {result.totals.usage.output:,}')
    console.print(f'  Cache read:  {result.totals.usage.cache_read:,}')
    console.print(f'  Cache write: {result.totals.usage.cache_write:,}')
    console.print(f'  Turns:       {result.totals.turn_count:,}\n')

    if result.by_project:
        _print_agg_table('By Project', result.by_project)
    if result.by_model:
        _print_agg_table('By Model', result.by_model)


@app.command()
def month() -> None:
    '''Show this month\'s token usage.'''
    from_dt, to_dt = _month_range()
    result = _run_report(from_dt, to_dt)

    console.print(f'\n[bold]This Month ({from_dt.strftime("%Y-%m")})[/bold]\n')
    console.print(f'Total tokens: [bold]{result.totals.usage.total:,}[/bold]')
    console.print(f'  Input:       {result.totals.usage.input:,}')
    console.print(f'  Output:      {result.totals.usage.output:,}')
    console.print(f'  Cache read:  {result.totals.usage.cache_read:,}')
    console.print(f'  Cache write: {result.totals.usage.cache_write:,}')
    console.print(f'  Turns:       {result.totals.turn_count:,}\n')

    if result.by_project:
        _print_agg_table('By Project', result.by_project)
    if result.by_model:
        _print_agg_table('By Model', result.by_model)
    if result.by_day:
        _print_agg_table('By Day', result.by_day, sort_by_total=False)


@app.command()
def report(
    period: Annotated[str, typer.Option('-p', '--period', help='today|7days|30days|month')] = '7days',
    from_date: Annotated[str | None, typer.Option('--from', help='YYYY-MM-DD')] = None,
    to_date: Annotated[str | None, typer.Option('--to', help='YYYY-MM-DD')] = None,
    refresh: Annotated[int | None, typer.Option('--refresh', help='Auto-refresh interval seconds')] = None,
) -> None:
    '''Token usage report.'''
    import time

    def _run() -> None:
        if from_date and to_date:
            from_dt = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc)
            to_dt = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc)
        elif period == 'today':
            from_dt, to_dt = _today_range()
        elif period == 'month':
            from_dt, to_dt = _month_range()
        elif period == '30days':
            from_dt, to_dt = _days_range(30)
        else:
            from_dt, to_dt = _days_range(7)

        result = _run_report(from_dt, to_dt)
        console.clear()
        console.print(f'\n[bold]Report: {period} ({from_dt.date()} to {to_dt.date()})[/bold]\n')
        console.print(f'Total tokens: [bold]{result.totals.usage.total:,}[/bold]  Turns: {result.totals.turn_count:,}\n')

        if result.by_day:
            _print_agg_table('By Day', result.by_day, sort_by_total=False)
        if result.by_project:
            _print_agg_table('By Project', result.by_project)
        if result.by_model:
            _print_agg_table('By Model', result.by_model)
        if result.by_tool:
            _print_agg_table('By Tool', result.by_tool)
        if result.by_mcp_server:
            _print_agg_table('By MCP Server', result.by_mcp_server)

    if refresh:
        while True:
            _run()
            console.print(f'\n[dim]Refreshing every {refresh}s. Ctrl+C to quit.[/dim]')
            time.sleep(refresh)
    else:
        _run()


@app.command()
def status(
    fmt: Annotated[str, typer.Option('--format', '-f', help='text|json')] = 'text',
) -> None:
    '''One-liner: today and month totals.'''
    today_result = _run_report(*_today_range())
    month_result = _run_report(*_month_range())

    if fmt == 'json':
        out = {
            'today': {
                'total': today_result.totals.usage.total,
                'input': today_result.totals.usage.input,
                'output': today_result.totals.usage.output,
                'cache_read': today_result.totals.usage.cache_read,
                'cache_write': today_result.totals.usage.cache_write,
                'turns': today_result.totals.turn_count,
            },
            'month': {
                'total': month_result.totals.usage.total,
                'input': month_result.totals.usage.input,
                'output': month_result.totals.usage.output,
                'cache_read': month_result.totals.usage.cache_read,
                'cache_write': month_result.totals.usage.cache_write,
                'turns': month_result.totals.turn_count,
            },
        }
        console.print(json.dumps(out, indent=2))
    else:
        console.print(
            f'Today: {today_result.totals.usage.total:,} tokens ({today_result.totals.turn_count} turns) | '
            f'Month: {month_result.totals.usage.total:,} tokens ({month_result.totals.turn_count} turns)'
        )


@app.command()
def export(
    fmt: Annotated[str, typer.Option('-f', '--format', help='csv|json')] = 'csv',
) -> None:
    '''Export token data for today, 7d, and 30d periods.'''
    from .export import run_export
    run_export(fmt=fmt)
