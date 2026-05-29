from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Static

from .aggregate import Aggregate, AggregateResult, aggregate_turns
from .format import format_tokens
from .parser import stream_turns

# ── gradient bar ──────────────────────────────────────────────────────────────

_GRAD = ['#0d1f3c', '#1a3a6e', '#2e6cb5', '#d97030', '#f5c040']
_BAR_W = 8


def _bar(value: int, max_val: int) -> Text:
    t = Text(no_wrap=True)
    if max_val == 0 or value == 0:
        t.append('▁' * _BAR_W, style='#1a1a1a')
        return t
    ratio = min(value / max_val, 1.0)
    filled = max(1, round(ratio * _BAR_W))
    for i in range(filled):
        p = i / (_BAR_W - 1) if _BAR_W > 1 else 1.0
        ci = round(p * (len(_GRAD) - 1))
        t.append('█', style=_GRAD[ci])
    t.append(' ' * (_BAR_W - filled))
    return t


# ── activity label colors ─────────────────────────────────────────────────────

_ACTIVITY_COLORS: dict[str, str] = {
    'Coding': '#f5c040',
    'Feature Dev': '#f5c040',
    'Exploration': '#4db8ff',
    'Debugging': '#ff6b6b',
    'Testing': '#f5c040',
    'Refactoring': '#f5c040',
    'Brainstorming': '#4db8ff',
    'Delegation': '#c0c0c0',
    'Planning': '#c0c0c0',
    'Git Ops': '#c0c0c0',
    'Build/Deploy': '#c0c0c0',
    'Conversation': '#808080',
    'General': '#505050',
}

# ── period helpers ────────────────────────────────────────────────────────────

_PERIODS: list[tuple[str, str]] = [
    ('today', 'Today'),
    ('7days', '7 Days'),
    ('30days', '30 Days'),
    ('month', 'Month'),
]
_PERIOD_LABELS = dict(_PERIODS)

_BORDER_COLORS = {
    'cyan': '#00cccc',
    'green': '#00cc66',
    'blue': '#4488ff',
    'magenta': '#cc44cc',
    'orange': '#cc7700',
}


def _today_range() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0), now


def _days_range(n: int) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=n - 1)).replace(hour=0, minute=0, second=0, microsecond=0), now


def _month_range() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now


# ── widgets ───────────────────────────────────────────────────────────────────

class PeriodBar(Static):
    def render_period(self, current: str) -> None:
        t = Text(no_wrap=True)
        t.append('  ')
        for key, label in _PERIODS:
            if key == current:
                t.append(f'[ {label} ]', style='bold #f5c040')
            else:
                t.append(f'  {label}  ', style='#505050')
            t.append('  ')
        self.update(t)


class SummaryWidget(Static):
    def update_data(self, result: AggregateResult, period_label: str) -> None:
        u = result.totals.usage
        denom = u.input + u.cache_read
        cache_pct = (u.cache_read / denom * 100) if denom > 0 else 0.0
        t = Text()
        t.append('token-burn', style='bold #f5c040')
        t.append(f'  {period_label}\n', style='#707070')
        t.append(f'{format_tokens(u.total):>8} total', style='bold #d0d0d0')
        t.append(f'   {result.totals.turn_count:,} turns', style='#a0a0a0')
        t.append(f'   {cache_pct:.1f}% cache hit\n', style='#4db8ff')
        t.append(f'{format_tokens(u.input):>8} in', style='#707070')
        t.append(f'   {format_tokens(u.output):>8} out', style='#707070')
        t.append(f'   {format_tokens(u.cache_read):>8} cached', style='#707070')
        t.append(f'   {format_tokens(u.cache_write):>8} written', style='#707070')
        self.update(t)


class PanelWidget(Static):
    def __init__(self, title: str, color: str, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._color = color

    def on_mount(self) -> None:
        hex_color = _BORDER_COLORS.get(self._color, '#888888')
        self.border_title = f'[{hex_color}]{self._title}[/{hex_color}]'
        self.add_class(self._color)

    def populate(
        self,
        data: dict[str, Aggregate],
        label_colors: dict[str, str] | None = None,
        sort_by_total: bool = True,
        label_width: int = 22,
        max_rows: int = 15,
    ) -> None:
        if not data:
            self.update('')
            return
        items = list(data.items())
        if sort_by_total:
            items.sort(key=lambda x: x[1].usage.total, reverse=True)
        items = items[:max_rows]
        max_val = max(v.usage.total for _, v in items) if items else 1

        t = Text(no_wrap=True)
        for name, agg in items:
            t.append_text(_bar(agg.usage.total, max_val))
            t.append(' ')
            color = (label_colors or {}).get(name, '#d0d0d0')
            t.append(name[:label_width].ljust(label_width), style=color)
            t.append(f' {format_tokens(agg.usage.total):>7}', style='#a0a0a0')
            t.append(f'  {agg.turn_count:>4}\n', style='#505050')
        self.update(t)

    def populate_days(self, data: dict[str, Aggregate]) -> None:
        if not data:
            self.update('')
            return
        items = sorted(data.items())
        max_val = max(v.usage.total for _, v in items) if items else 1

        t = Text(no_wrap=True)
        for name, agg in items:
            t.append_text(_bar(agg.usage.total, max_val))
            t.append(' ')
            t.append(name, style='#d0d0d0')
            t.append(f'  {format_tokens(agg.usage.total):>8}', style='#f5c040')
            t.append(f'  {agg.turn_count:>4}\n', style='#505050')
        self.update(t)


# ── app ───────────────────────────────────────────────────────────────────────

_CSS = """
Screen {
    background: #080808;
    color: #d0d0d0;
    overflow-y: scroll;
}

PeriodBar {
    height: 1;
    background: #080808;
    padding: 0 0;
    margin: 0 0 1 0;
}

SummaryWidget {
    height: auto;
    border: solid #cc7700;
    padding: 0 1;
    margin: 0 0 1 0;
}

#columns {
    height: auto;
}

#left-col, #right-col {
    width: 1fr;
}

PanelWidget {
    height: auto;
    padding: 0 1;
    margin: 0 1 1 0;
}

PanelWidget.cyan    { border: solid #00cccc; }
PanelWidget.green   { border: solid #00cc66; }
PanelWidget.blue    { border: solid #4488ff; }
PanelWidget.magenta { border: solid #cc44cc; }
"""


class TokenBurnApp(App[None]):
    TITLE = 'token-burn'
    CSS = _CSS
    BINDINGS = [
        Binding('left', 'period_prev', 'Prev'),
        Binding('right', 'period_next', 'Next'),
        Binding('1', 'period_today', 'Today'),
        Binding('2', 'period_7days', '7 Days'),
        Binding('3', 'period_30days', '30 Days'),
        Binding('4', 'period_month', 'Month'),
        Binding('r', 'refresh', 'Refresh'),
        Binding('q', 'quit', 'Quit'),
    ]

    period: reactive[str] = reactive('7days')

    def compose(self) -> ComposeResult:
        yield PeriodBar(id='period_bar')
        yield SummaryWidget(id='summary')
        with Horizontal(id='columns'):
            with Vertical(id='left-col'):
                yield PanelWidget('Daily Activity', 'cyan', id='days')
                yield PanelWidget('By Activity', 'blue', id='activity')
                yield PanelWidget('Core Tools', 'cyan', id='tools')
                yield PanelWidget('MCP Servers', 'magenta', id='mcp')
            with Vertical(id='right-col'):
                yield PanelWidget('By Project', 'green', id='projects')
                yield PanelWidget('By Model', 'green', id='models')
                yield PanelWidget('Shell Commands', 'magenta', id='shell')
        yield Footer()

    def on_mount(self) -> None:
        self.query_one('#period_bar', PeriodBar).render_period(self.period)
        self.load_data()

    def watch_period(self, value: str) -> None:
        self.query_one('#period_bar', PeriodBar).render_period(value)
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
        self.query_one('#summary', SummaryWidget).update_data(result, _PERIOD_LABELS[p])
        self.query_one('#days', PanelWidget).populate_days(result.by_day)
        self.query_one('#activity', PanelWidget).populate(result.by_activity, label_colors=_ACTIVITY_COLORS)
        self.query_one('#tools', PanelWidget).populate(result.by_tool)
        self.query_one('#mcp', PanelWidget).populate(result.by_mcp_server)
        self.query_one('#projects', PanelWidget).populate(result.by_project)
        self.query_one('#models', PanelWidget).populate(result.by_model)
        self.query_one('#shell', PanelWidget).populate(result.by_shell_cmd)

    def action_period_today(self) -> None: self.period = 'today'
    def action_period_7days(self) -> None: self.period = '7days'
    def action_period_30days(self) -> None: self.period = '30days'
    def action_period_month(self) -> None: self.period = 'month'
    def action_refresh(self) -> None: self.load_data()

    def action_period_prev(self) -> None:
        keys = [k for k, _ in _PERIODS]
        self.period = keys[(keys.index(self.period) - 1) % len(keys)]

    def action_period_next(self) -> None:
        keys = [k for k, _ in _PERIODS]
        self.period = keys[(keys.index(self.period) + 1) % len(keys)]
