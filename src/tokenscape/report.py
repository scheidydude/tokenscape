from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .aggregate import AggregateResult
from .format import format_tokens
from .patterns import (
    activity_transitions,
    file_edit_frequency,
    growth_signals,
    model_activity_breakdown,
    model_efficiency_signals,
    project_model_breakdown,
    prompt_action_verbs,
    prompt_bigrams,
    session_ramp_stats,
    shell_automation_candidates,
)
from .types import Turn

if TYPE_CHECKING:
    pass


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [
        max(len(h), max((len(r[i]) for r in rows), default=0))
        for i, h in enumerate(headers)
    ]
    header = '| ' + ' | '.join(h.ljust(w) for h, w in zip(headers, widths)) + ' |'
    sep = '| ' + ' | '.join('-' * w for w in widths) + ' |'
    body = '\n'.join(
        '| ' + ' | '.join(r[i].ljust(widths[i]) for i in range(len(headers))) + ' |'
        for r in rows
    )
    return f'{header}\n{sep}\n{body}'


def generate(
    turns: list[Turn],
    sessions: list[list[Turn]],
    result: AggregateResult,
    from_dt: datetime,
    to_dt: datetime,
    period_label: str,
    top: int = 8,
    labels_config: dict[str, str] | None = None,
    summarize_config: dict[str, str] | None = None,
    force_summary: bool = False,
    tool_label: str = 'CLAUDE',
) -> str:
    parts: list[str] = []

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    parts.append(
        f'# tokenscape report — {tool_label} · {period_label} ({from_dt.date()} to {to_dt.date()})\n'
        f'*Generated {now}*'
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    u = result.totals.usage
    denom = u.input + u.cache_read
    cache_pct = u.cache_read / denom * 100 if denom else 0.0
    summary_line = (
        f'**{format_tokens(u.total)}** total tokens · '
        f'**{result.totals.turn_count:,}** turns · '
        f'**{cache_pct:.1f}%** cache hit'
    )

    model_rows = [
        [m, f'{a.turn_count:,}', format_tokens(a.usage.total),
         format_tokens(int(a.usage.total / a.turn_count)) if a.turn_count else '0']
        for m, a in sorted(result.by_model.items(), key=lambda x: -x[1].usage.total)[:top]
    ] if result.by_model else []

    section = f'## Summary\n\n{summary_line}'
    if model_rows:
        section += '\n\n' + _md_table(['Model', 'Turns', 'Tokens', 'Avg/turn'], model_rows)
    parts.append(section)

    # ── Projects ──────────────────────────────────────────────────────────────
    if result.by_project:
        proj_rows = [
            [name, f'{a.turn_count:,}', format_tokens(a.usage.total)]
            for name, a in sorted(result.by_project.items(), key=lambda x: -x[1].usage.total)[:top]
        ]
        parts.append('## Projects\n\n' + _md_table(['Project', 'Turns', 'Tokens'], proj_rows))

    # ── Workflow ──────────────────────────────────────────────────────────────
    transitions = activity_transitions(sessions, top_n=top)
    ramp = session_ramp_stats(sessions)
    workflow_parts: list[str] = ['## Workflow']
    if transitions:
        tr_rows = [
            [t.from_activity, t.to_activity, str(t.count), f'{t.pct:.0%}']
            for t in transitions
        ]
        workflow_parts.append(_md_table(['From', 'To', 'Count', '%'], tr_rows))
    workflow_parts.append(
        f'**Session ramp** — mean {ramp.mean:.1f} turns to first edit · '
        f'p90 {ramp.p90:.0f} · {ramp.session_count} sessions'
    )
    parts.append('\n\n'.join(workflow_parts))

    # ── Growth Signals ────────────────────────────────────────────────────────
    signals = growth_signals(turns)
    if signals:
        sig_rows = [[s.project, s.kind.replace('_', ' '), s.description] for s in signals]
        parts.append('## Growth Signals\n\n' + _md_table(['Project', 'Signal', 'Detail'], sig_rows))
    else:
        parts.append('## Growth Signals\n\n*No signals flagged.*')

    # ── Model Efficiency ──────────────────────────────────────────────────────
    stats = model_activity_breakdown(turns)
    if stats:
        me_rows = [
            [s.model, f'{s.total_turns:,}', format_tokens(s.total_tokens),
             format_tokens(int(s.avg_tokens)),
             '<br>'.join(f'{a} {pct:.0%}' for a, pct in s.top_activities(13))]
            for s in stats[:top]
        ]
        me_section = '## Model Efficiency\n\n' + _md_table(
            ['Model', 'Turns', 'Tokens', 'Avg/turn', 'Activities'], me_rows
        )
        eff = model_efficiency_signals(stats)
        if eff:
            eff_rows = [[sig.model, sig.kind.replace('_', ' '), sig.description] for sig in eff]
            me_section += '\n\n' + _md_table(['Model', 'Signal', 'Detail'], eff_rows)

        proj_breakdown = project_model_breakdown(turns)
        if proj_breakdown:
            pb_rows: list[list[str]] = []
            for proj, proj_stats in proj_breakdown.items():
                for i, s in enumerate(proj_stats):
                    pb_rows.append([
                        proj if i == 0 else '',
                        s.model,
                        f'{s.total_turns:,}',
                        format_tokens(s.total_tokens),
                        format_tokens(int(s.avg_tokens)),
                        '<br>'.join(f'{a} {pct:.0%}' for a, pct in s.top_activities(13)),
                    ])
            me_section += '\n\n**By project**\n\n' + _md_table(
                ['Project', 'Model', 'Turns', 'Tokens', 'Avg/turn', 'Activities'], pb_rows
            )

        parts.append(me_section)

    # ── Patterns ──────────────────────────────────────────────────────────────
    pattern_blocks: list[str] = ['## Patterns']
    shell_top = min(top, 5)

    candidates = shell_automation_candidates(turns, min_count=3)
    if candidates:
        shell_rows = [
            [c.command, str(c.count), ', '.join(c.projects[:2])]
            for c in candidates[:shell_top]
        ]
        pattern_blocks.append('**Top shell commands**\n\n' + _md_table(['Command', 'Runs', 'Projects'], shell_rows))

    edits = file_edit_frequency(turns, top_n=shell_top)
    if edits:
        pattern_blocks.append('**Hottest files**\n\n' + _md_table(['File', 'Edits'], [[f, str(c)] for f, c in edits]))

    verbs = prompt_action_verbs(turns, top_n=10)
    if verbs:
        pattern_blocks.append('**Prompt verbs**\n\n' + _md_table(['Verb', 'Count'], [[v, str(c)] for v, c in verbs]))

    bigrams = prompt_bigrams(turns, top_n=10)
    if bigrams:
        pattern_blocks.append('**Prompt bigrams**\n\n' + _md_table(['Bigram', 'Count'], [[b, str(c)] for b, c in bigrams]))

    if len(pattern_blocks) > 1:
        parts.append('\n\n'.join(pattern_blocks))

    # ── Intent Clusters (optional) ────────────────────────────────────────────
    try:
        from .semantic import _MODEL, analyze, label_cluster  # optional dep

        prompt_count = sum(1 for t in turns if len(t.user_text.strip().split()) >= 3)
        if prompt_count >= 4:
            examples_map, counts_map, k_used = analyze(turns)
            if examples_map:
                cluster_lines = [f'## Intent Clusters\n\n*{prompt_count} prompts · k={k_used} · {_MODEL}*']
                for cluster_id, exs in examples_map.items():
                    count = counts_map[cluster_id]
                    pct = count / prompt_count * 100 if prompt_count else 0
                    lbl = ''
                    if labels_config:
                        result_lbl = label_cluster(exs, labels_config)
                        if result_lbl:
                            lbl = f' — {result_lbl}'
                    cluster_lines.append(
                        f'**Cluster {cluster_id + 1}{lbl}** ({count} prompts, {pct:.0f}%)\n'
                        + '\n'.join(
                            f'- *{(ex[:100] + "…") if len(ex) > 100 else ex}*'
                            for ex in exs[:2]
                        )
                    )
                parts.append('\n\n'.join(cluster_lines))
    except ModuleNotFoundError:
        import sys
        print('[tokenscape] Intent Clusters skipped: install "tokenscape[semantic]"', file=sys.stderr)

    # ── AI Insights (optional) ────────────────────────────────────────────────
    if summarize_config:
        try:
            from .semantic import generate_ai_summary

            u2 = result.totals.usage
            denom2 = u2.input + u2.cache_read
            cache_pct2 = u2.cache_read / denom2 * 100 if denom2 else 0.0

            _stats = model_activity_breakdown(turns)
            _signals = growth_signals(turns)
            _eff = model_efficiency_signals(_stats)
            _candidates = shell_automation_candidates(turns, min_count=3)
            _verbs = prompt_action_verbs(turns, top_n=10)
            _ramp_stats = session_ramp_stats(sessions)

            context = {
                'period': f'{from_dt.date()} to {to_dt.date()}',
                'total_tokens': u2.total,
                'total_turns': result.totals.turn_count,
                'cache_hit_pct': round(cache_pct2, 1),
                'models': [
                    {
                        'model': s.model,
                        'turns': s.total_turns,
                        'total_tokens': s.total_tokens,
                        'avg_tokens_per_turn': int(s.avg_tokens),
                        'top_activities': [
                            {'activity': a, 'pct': round(p * 100, 1)}
                            for a, p in s.top_activities(3)
                        ],
                    }
                    for s in _stats[:5]
                ],
                'top_projects': [
                    {'project': name, 'turns': a.turn_count, 'total_tokens': a.usage.total}
                    for name, a in sorted(result.by_project.items(), key=lambda x: -x[1].usage.total)[:5]
                ],
                'growth_signals': [
                    {'project': s.project, 'kind': s.kind, 'description': s.description}
                    for s in _signals
                ],
                'model_efficiency_signals': [
                    {'model': sig.model, 'kind': sig.kind, 'description': sig.description}
                    for sig in _eff
                ],
                'shell_automation_candidates': [
                    {'command': c.command, 'count': c.count}
                    for c in _candidates[:5]
                ],
                'prompt_verbs': [{'verb': v, 'count': c} for v, c in _verbs],
                'session_ramp_mean': round(_ramp_stats.mean, 1),
                'session_ramp_p90': round(_ramp_stats.p90, 0),
                'session_count': _ramp_stats.session_count,
            }

            ai_text = generate_ai_summary(context, summarize_config, force=force_summary)
            if ai_text:
                parts.append(f'## AI Insights\n\n{ai_text}')
        except Exception as e:
            import sys
            print(f'[tokenscape] AI Insights error: {e!r}', file=sys.stderr)

    return '\n\n'.join(parts) + '\n'
