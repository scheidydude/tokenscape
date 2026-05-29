from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

from .classifier import classify
from .types import Aggregate, TokenUsage, Turn

_MCP_RE = re.compile(r'^mcp__([^_]+)__')
_SHELL_CORE_TOOLS = {
    'Read', 'Edit', 'Write', 'Bash', 'Grep', 'Glob',
    'Task', 'Agent', 'WebSearch', 'WebFetch',
    'EnterPlanMode', 'ExitPlanMode', 'TaskCreate', 'TaskUpdate',
    'TaskGet', 'TaskList', 'TaskStop', 'TaskOutput',
    'NotebookEdit', 'LSP', 'Monitor',
}


@dataclass
class AggregateResult:
    by_day: dict[str, Aggregate] = field(default_factory=lambda: defaultdict(Aggregate))
    by_project: dict[str, Aggregate] = field(default_factory=lambda: defaultdict(Aggregate))
    by_model: dict[str, Aggregate] = field(default_factory=lambda: defaultdict(Aggregate))
    by_tool: dict[str, Aggregate] = field(default_factory=lambda: defaultdict(Aggregate))
    by_shell_cmd: dict[str, Aggregate] = field(default_factory=lambda: defaultdict(Aggregate))
    by_mcp_server: dict[str, Aggregate] = field(default_factory=lambda: defaultdict(Aggregate))
    by_activity: dict[str, Aggregate] = field(default_factory=lambda: defaultdict(Aggregate))
    totals: Aggregate = field(default_factory=Aggregate)


def _shell_cmd(tool_input: object) -> str | None:
    if not isinstance(tool_input, dict):
        return None
    cmd = tool_input.get('command', '')
    if not isinstance(cmd, str) or not cmd.strip():
        return None
    return cmd.strip().split()[0]


def _accumulate(agg: Aggregate, usage: TokenUsage) -> None:
    agg.usage = agg.usage + usage
    agg.turn_count += 1


def aggregate_turns(turns: Iterable[Turn]) -> AggregateResult:
    result = AggregateResult()

    for turn in turns:
        day = turn.timestamp.strftime('%Y-%m-%d')
        _accumulate(result.by_day[day], turn.usage)
        _accumulate(result.by_project[turn.project or 'unknown'], turn.usage)
        _accumulate(result.by_model[turn.model or 'unknown'], turn.usage)
        _accumulate(result.totals, turn.usage)

        for tool_name in turn.tools_used:
            m = _MCP_RE.match(tool_name)
            if m:
                _accumulate(result.by_mcp_server[m.group(1)], turn.usage)
            elif tool_name in _SHELL_CORE_TOOLS or not tool_name.startswith('mcp__'):
                _accumulate(result.by_tool[tool_name], turn.usage)

        for cmd in turn.bash_inputs:
            first = cmd.split()[0] if cmd.strip() else None
            if first:
                _accumulate(result.by_shell_cmd[first], turn.usage)

        activity = classify(turn, turn.bash_inputs).value
        _accumulate(result.by_activity[activity], turn.usage)

    return result
