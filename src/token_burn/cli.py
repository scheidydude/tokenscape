from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .aggregate import AggregateResult, aggregate_turns
from .parser import list_projects, stream_sessions, stream_turns
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


def _resolve_period(
    period: str,
    from_date: str | None,
    to_date: str | None,
) -> tuple[datetime, datetime]:
    if from_date and to_date:
        return (
            datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc),
            datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc),
        )
    if period == 'today':
        return _today_range()
    if period == 'month':
        return _month_range()
    if period == '90days':
        return _days_range(90)
    if period == '30days':
        return _days_range(30)
    return _days_range(7)


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
        if result.by_activity:
            _print_agg_table('By Activity', result.by_activity)
        if result.by_shell_cmd:
            _print_agg_table('By Shell Command', result.by_shell_cmd)

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


def _print_project_list(projects: list[tuple[str, datetime]]) -> None:
    for i, (name, last_active) in enumerate(projects, 1):
        console.print(f'  [bold cyan]{i:2}.[/bold cyan] {name:<40} [dim]{last_active.strftime("%Y-%m-%d")}[/dim]')


def _prompt_project_selection(projects: list[tuple[str, datetime]]) -> str | None:
    _print_project_list(projects)
    console.print()
    while True:
        raw = console.input('[bold]Select # or type search term (q to quit):[/bold] ').strip()
        if raw.lower() == 'q':
            return None
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(projects):
                return projects[idx][0]
            console.print(f'[red]Enter a number between 1 and {len(projects)}[/red]')
            continue
        matches = [(p, d) for p, d in projects if raw.lower() in p.lower()]
        if len(matches) == 1:
            return matches[0][0]
        if matches:
            console.print(f'[yellow]{len(matches)} matches:[/yellow]')
            projects = matches
            _print_project_list(projects)
        else:
            console.print(f'[red]No match for "{raw}"[/red]')


def _print_project_report(
    name: str,
    period: str,
    from_dt: datetime,
    to_dt: datetime,
    result: AggregateResult,
) -> None:
    u = result.totals.usage
    console.print(f'\n[bold cyan]{name}[/bold cyan]  [dim]{period}  {from_dt.date()} to {to_dt.date()}[/dim]\n')
    console.print(
        f'Total: [bold]{u.total:,}[/bold]'
        f'  Input: {u.input:,}'
        f'  Output: {u.output:,}'
        f'  Cache read: {u.cache_read:,}'
        f'  Cache write: {u.cache_write:,}'
        f'  Turns: {result.totals.turn_count:,}\n'
    )
    if result.by_day:
        _print_agg_table('By Day', result.by_day, sort_by_total=False)
    if result.by_activity:
        _print_agg_table('By Activity', result.by_activity)
    if result.by_tool:
        _print_agg_table('By Tool', result.by_tool)
    if result.by_shell_cmd:
        _print_agg_table('By Shell Command', result.by_shell_cmd)
    if result.by_mcp_server:
        _print_agg_table('By MCP Server', result.by_mcp_server)


@app.command()
def project(
    name: Annotated[str | None, typer.Argument(help='Project name or search term')] = None,
    period: Annotated[str, typer.Option('-p', '--period', help='today|7days|30days|month')] = '30days',
    from_date: Annotated[str | None, typer.Option('--from', help='YYYY-MM-DD')] = None,
    to_date: Annotated[str | None, typer.Option('--to', help='YYYY-MM-DD')] = None,
) -> None:
    '''Token breakdown for a specific project: by day, activity, and tool.'''
    projects = list_projects()
    if not projects:
        console.print('[red]No projects found.[/red]')
        raise typer.Exit(1)

    selected: str | None = None

    if name:
        matches = [(p, d) for p, d in projects if name.lower() in p.lower()]
        if len(matches) == 1:
            selected = matches[0][0]
        elif len(matches) > 1:
            console.print(f'[yellow]Multiple matches for "{name}":[/yellow]\n')
            selected = _prompt_project_selection(matches)
        else:
            console.print(f'[yellow]No match for "{name}". Recent projects:[/yellow]\n')
            selected = _prompt_project_selection(projects)
    else:
        console.print('[bold]Recent projects:[/bold]\n')
        selected = _prompt_project_selection(projects)

    if not selected:
        return

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

    turns = (t for t in stream_turns(from_dt=from_dt, to_dt=to_dt) if t.project == selected)
    result = aggregate_turns(turns)

    if result.totals.turn_count == 0:
        console.print(f'[yellow]No activity for "{selected}" in this period.[/yellow]')
        return

    _print_project_report(selected, period, from_dt, to_dt, result)


@app.command()
def patterns(
    period: Annotated[str, typer.Option('-p', '--period', help='today|7days|30days|month')] = '30days',
    from_date: Annotated[str | None, typer.Option('--from', help='YYYY-MM-DD')] = None,
    to_date: Annotated[str | None, typer.Option('--to', help='YYYY-MM-DD')] = None,
    min_count: Annotated[int, typer.Option('--min', help='Min occurrences for shell candidates')] = 3,
) -> None:
    '''Shell automation candidates, hottest files, and user prompt patterns.'''
    from .patterns import (
        file_edit_frequency,
        prompt_action_verbs,
        prompt_bigrams,
        repeated_prompts,
        shell_automation_candidates,
    )

    from_dt, to_dt = _resolve_period(period, from_date, to_date)
    turns = list(stream_turns(from_dt=from_dt, to_dt=to_dt))

    candidates = shell_automation_candidates(turns, min_count=min_count)
    if candidates:
        table = Table(title=f'Claude\'s Top Bash Operations  (≥{min_count} runs)', show_header=True, header_style='bold')
        table.add_column('Command', style='cyan')
        table.add_column('Runs', justify='right')
        table.add_column('Projects')
        table.add_column('Example')
        for c in candidates:
            ex = (c.examples[0] if c.examples else '').replace('\n', ' ')
            ex = ex[:60] + '…' if len(ex) > 60 else ex
            table.add_row(c.command, str(c.count), ', '.join(c.projects[:3]), ex)
        console.print(table)
    else:
        console.print(f'[dim]No shell commands repeated ≥{min_count} times in this period.[/dim]')

    edits = file_edit_frequency(turns)
    if edits:
        console.print()
        table = Table(title='Hottest Files  (by edit count)', show_header=True, header_style='bold')
        table.add_column('File', style='cyan')
        table.add_column('Edits', justify='right')
        for f, count in edits:
            table.add_row(f, str(count))
        console.print(table)

    console.print()
    verbs = prompt_action_verbs(turns)
    if verbs:
        table = Table(title='User Prompt Verbs  (leading intent word)', show_header=True, header_style='bold')
        table.add_column('Verb', style='cyan')
        table.add_column('Count', justify='right')
        for verb, count in verbs:
            table.add_row(verb, str(count))
        console.print(table)

    bigrams = prompt_bigrams(turns)
    if bigrams:
        console.print()
        table = Table(title='User Prompt Bigrams  (top word pairs, stopwords removed)', show_header=True, header_style='bold')
        table.add_column('Bigram', style='cyan')
        table.add_column('Count', justify='right')
        for bigram, count in bigrams:
            table.add_row(bigram, str(count))
        console.print(table)

    repeated = repeated_prompts(turns)
    if repeated:
        console.print()
        table = Table(title='Repeated Prompts  (exact match, ≥2 times)', show_header=True, header_style='bold')
        table.add_column('Prompt', style='cyan')
        table.add_column('Count', justify='right')
        for text, count in repeated[:20]:
            display = text[:80] + '…' if len(text) > 80 else text
            table.add_row(display, str(count))
        console.print(table)


@app.command()
def workflow(
    period: Annotated[str, typer.Option('-p', '--period', help='today|7days|30days|month')] = '30days',
    from_date: Annotated[str | None, typer.Option('--from', help='YYYY-MM-DD')] = None,
    to_date: Annotated[str | None, typer.Option('--to', help='YYYY-MM-DD')] = None,
) -> None:
    '''Activity transition sequences and session ramp time.'''
    from .patterns import activity_transitions, session_ramp_stats

    from_dt, to_dt = _resolve_period(period, from_date, to_date)
    sessions = list(stream_sessions(from_dt=from_dt, to_dt=to_dt))

    transitions = activity_transitions(sessions)
    if transitions:
        table = Table(
            title=f'Activity Transitions  ({len(sessions)} sessions)',
            show_header=True,
            header_style='bold',
        )
        table.add_column('From', style='cyan')
        table.add_column('→', style='dim')
        table.add_column('To', style='cyan')
        table.add_column('Count', justify='right')
        table.add_column('%', justify='right')
        for t in transitions:
            table.add_row(t.from_activity, '→', t.to_activity, str(t.count), f'{t.pct:.0%}')
        console.print(table)
    else:
        console.print('[dim]No activity sequences found in this period.[/dim]')

    console.print()
    ramp = session_ramp_stats(sessions)
    console.print(f'[bold]Session Ramp[/bold]  ({ramp.session_count} sessions)')
    console.print(f'  Mean turns before first edit: [bold]{ramp.mean:.1f}[/bold]')
    console.print(f'  P90: [bold]{ramp.p90:.0f}[/bold]')


@app.command()
def growth(
    period: Annotated[str, typer.Option('-p', '--period', help='today|7days|30days|month')] = '30days',
    from_date: Annotated[str | None, typer.Option('--from', help='YYYY-MM-DD')] = None,
    to_date: Annotated[str | None, typer.Option('--to', help='YYYY-MM-DD')] = None,
) -> None:
    '''Per-project efficiency gaps: debug/test ratio, conversation overhead.'''
    from .patterns import growth_signals

    from_dt, to_dt = _resolve_period(period, from_date, to_date)
    turns = list(stream_turns(from_dt=from_dt, to_dt=to_dt))

    signals = growth_signals(turns)
    if signals:
        table = Table(title='Growth Signals', show_header=True, header_style='bold')
        table.add_column('Project', style='cyan')
        table.add_column('Signal')
        table.add_column('Detail')
        for s in signals:
            table.add_row(s.project, s.kind, s.description)
        console.print(table)
    else:
        console.print('[green]No growth signals flagged in this period.[/green]')


@app.command()
def semantic(
    period: Annotated[str, typer.Option('-p', '--period', help='today|7days|30days|90days|month')] = '90days',
    from_date: Annotated[str | None, typer.Option('--from', help='YYYY-MM-DD')] = None,
    to_date: Annotated[str | None, typer.Option('--to', help='YYYY-MM-DD')] = None,
    k: Annotated[int | None, typer.Option('-k', help='Cluster count (auto-selected by default)')] = None,
    project: Annotated[str | None, typer.Option('--project', help='Scope to one project')] = None,
) -> None:
    '''Semantic intent clustering of user prompts. Requires: pip install "token-burn[semantic]"'''
    from_dt, to_dt = _resolve_period(period, from_date, to_date)
    turns = list(stream_turns(from_dt=from_dt, to_dt=to_dt))

    if project:
        turns = [t for t in turns if t.project == project]

    n_prompts = sum(1 for t in turns if t.user_text.strip())
    if n_prompts < 4:
        console.print(f'[yellow]Only {n_prompts} prompts in this period — need at least 4 for clustering.[/yellow]')
        raise typer.Exit(0)

    try:
        from .semantic import _MODEL, analyze
    except ModuleNotFoundError:
        console.print('[red]Semantic analysis requires extra dependencies:[/red]')
        console.print('  pip install "token-burn[semantic]"')
        raise typer.Exit(1)

    console.print(f'[dim]Embedding {n_prompts} prompts ({_MODEL})…[/dim]')

    try:
        examples, counts, k_used = analyze(turns, k=k)
    except ModuleNotFoundError:
        console.print('[red]Missing dependencies. Run:[/red]')
        console.print('  pip install "token-burn[semantic]"')
        raise typer.Exit(1)

    if not examples:
        console.print('[yellow]No prompts to cluster.[/yellow]')
        return

    scope = f'project={project}' if project else 'all projects'
    console.print(
        f'\n[bold]Intent Clusters[/bold]  '
        f'({n_prompts} prompts, k={k_used}, {scope})\n'
    )

    for cluster_id, cluster_examples in examples.items():
        count = counts[cluster_id]
        pct = count / n_prompts * 100
        console.print(f'[bold cyan]Cluster {cluster_id + 1}[/bold cyan]  ({count} prompts, {pct:.0f}%)')
        for ex in cluster_examples:
            display = ex[:100] + '…' if len(ex) > 100 else ex
            console.print(f'  [dim]→[/dim] {display!r}')
        console.print()


@app.command()
def export(
    fmt: Annotated[str, typer.Option('-f', '--format', help='csv|json')] = 'csv',
) -> None:
    '''Export token data for today, 7d, and 30d periods.'''
    from .export import run_export
    run_export(fmt=fmt)
