from __future__ import annotations

from datetime import datetime, timezone

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Label, Static

from .aggregate import AggregateResult, aggregate_turns
from .format import format_tokens
from .parser import stream_turns


def _today_range() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0), now


def _days_range(n: int) -> tuple[datetime, datetime]:
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=n - 1)).replace(hour=0, minute=0, second=0, microsecond=0), now


def _month_range() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now


_PERIODS = ['today', '7days', '30days', 'month']
_PERIOD_LABELS = {'today': 'Today', '7days': '7 Days', '30days': '30 Days', 'month': 'Month'}


class SummaryPanel(Static):
    def update_data(self, result: AggregateResult) -> None:
        u = result.totals.usage
        self.update(
            f'Total: [bold]{format_tokens(u.total)}[/bold]  '
            f'Input: {format_tokens(u.input)}  '
            f'Output: {format_tokens(u.output)}  '
            f'Cache R: {format_tokens(u.cache_read)}  '
            f'Cache W: {format_tokens(u.cache_write)}  '
            f'Turns: {result.totals.turn_count}'
        )


class AggTable(DataTable):
    def populate(self, title: str, data: dict[str, object], sort_by_total: bool = True) -> None:
        self.clear(columns=True)
        self.add_columns('Name', 'Input', 'Output', 'Cache R', 'Cache W', 'Total')
        from .types import Aggregate
        items = [(k, v) for k, v in data.items() if isinstance(v, Aggregate)]
        if sort_by_total:
            items.sort(key=lambda x: x[1].usage.total, reverse=True)
        for name, agg in items[:20]:
            u = agg.usage
            self.add_row(name, format_tokens(u.input), format_tokens(u.output),
                         format_tokens(u.cache_read), format_tokens(u.cache_write),
                         format_tokens(u.total))


class TokenBurnApp(App[None]):
    TITLE = 'claude-token-burn'
    BINDINGS = [
        Binding('1', 'set_period_today', 'Today'),
        Binding('2', 'set_period_7days', '7 Days'),
        Binding('3', 'set_period_30days', '30 Days'),
        Binding('4', 'set_period_month', 'Month'),
        Binding('r', 'refresh_data', 'Refresh'),
        Binding('q', 'quit', 'Quit'),
    ]

    period: reactive[str] = reactive('7days')

    def compose(self) -> ComposeResult:
        yield Header()
        yield SummaryPanel(id='summary')
        with Horizontal():
            with Vertical():
                yield Label('Projects')
                yield AggTable(id='projects')
            with Vertical():
                yield Label('Models')
                yield AggTable(id='models')
        with Horizontal():
            with Vertical():
                yield Label('Tools')
                yield AggTable(id='tools')
            with Vertical():
                yield Label('MCP Servers')
                yield AggTable(id='mcp')
        with Horizontal():
            with Vertical():
                yield Label('Activity')
                yield AggTable(id='activity')
            with Vertical():
                yield Label('Shell Commands')
                yield AggTable(id='shell')
        with Vertical():
            yield Label('By Day')
            yield AggTable(id='days')
        yield Footer()

    def on_mount(self) -> None:
        self.load_data()

    def watch_period(self, value: str) -> None:
        self.sub_title = _PERIOD_LABELS.get(value, value)
        self.load_data()

    def load_data(self) -> None:
        p = self.period
        if p == 'today':
            from_dt, to_dt = _today_range()
        elif p == '30days':
            from_dt, to_dt = _days_range(30)
        elif p == 'month':
            from_dt, to_dt = _month_range()
        else:
            from_dt, to_dt = _days_range(7)

        result = aggregate_turns(stream_turns(from_dt=from_dt, to_dt=to_dt))
        self.query_one('#summary', SummaryPanel).update_data(result)
        self.query_one('#projects', AggTable).populate('Projects', result.by_project)
        self.query_one('#models', AggTable).populate('Models', result.by_model)
        self.query_one('#tools', AggTable).populate('Tools', result.by_tool)
        self.query_one('#mcp', AggTable).populate('MCP', result.by_mcp_server)
        self.query_one('#activity', AggTable).populate('Activity', result.by_activity)
        self.query_one('#shell', AggTable).populate('Shell Commands', result.by_shell_cmd)
        self.query_one('#days', AggTable).populate('Days', result.by_day, sort_by_total=False)

    def action_set_period_today(self) -> None:
        self.period = 'today'

    def action_set_period_7days(self) -> None:
        self.period = '7days'

    def action_set_period_30days(self) -> None:
        self.period = '30days'

    def action_set_period_month(self) -> None:
        self.period = 'month'

    def action_refresh_data(self) -> None:
        self.load_data()
