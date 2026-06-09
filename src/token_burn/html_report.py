from __future__ import annotations

import html
import json
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

_ACTIVITY_COLORS = {
    'Coding': '#6366f1',
    'Exploration': '#06b6d4',
    'Conversation': '#f59e0b',
    'General': '#84cc16',
    'Testing': '#ec4899',
    'Git Ops': '#8b5cf6',
    'Build/Deploy': '#f97316',
}

_DEFAULT_COLOR = '#94a3b8'


def _esc(s: str) -> str:
    return html.escape(str(s))


def _activity_color(activity: str) -> str:
    return _ACTIVITY_COLORS.get(activity, _DEFAULT_COLOR)


def _html_table(headers: list[str], rows: list[list[str]], table_id: str = '', sortable: bool = True) -> str:
    tid = f' id="{table_id}"' if table_id else ''
    sort_class = ' sortable' if sortable else ''
    th_cells = ''.join(
        f'<th class="sortable-header" data-col="{i}">{_esc(h)}<span class="sort-icon">⇅</span></th>'
        for i, h in enumerate(headers)
    )
    thead = f'<thead><tr>{th_cells}</tr></thead>'
    tbody_rows = []
    for row in rows:
        cells = ''.join(f'<td>{_esc(c)}</td>' for c in row)
        tbody_rows.append(f'<tr>{cells}</tr>')
    tbody = f'<tbody>{"".join(tbody_rows)}</tbody>'
    return f'<table{tid} class="data-table{sort_class}">{thead}{tbody}</table>'


def _activities_bar(activities: list[tuple[str, float]]) -> str:
    bars = []
    for act, pct in activities:
        color = _activity_color(act)
        pct_val = pct * 100
        bars.append(
            f'<div class="act-bar" style="width:{pct_val:.1f}%;background:{color}" '
            f'title="{_esc(act)} {pct_val:.0f}%"></div>'
        )
    return f'<div class="act-stack">{"".join(bars)}</div>'


def _chart_data_json(stats: list) -> str:
    data = []
    for s in stats:
        activities = s.top_activities(13)
        data.append({
            'model': s.model,
            'turns': s.total_turns,
            'tokens': s.total_tokens,
            'avg': int(s.avg_tokens),
            'activities': [{'name': a, 'pct': round(p * 100, 1)} for a, p in activities],
        })
    return json.dumps(data)


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
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    u = result.totals.usage
    denom = u.input + u.cache_read
    cache_pct = u.cache_read / denom * 100 if denom else 0.0

    # ── collect all section data ──────────────────────────────────────────────
    model_rows = [
        [m, f'{a.turn_count:,}', format_tokens(a.usage.total),
         format_tokens(int(a.usage.total / a.turn_count)) if a.turn_count else '0']
        for m, a in sorted(result.by_model.items(), key=lambda x: -x[1].usage.total)[:top]
    ] if result.by_model else []

    proj_rows = [
        [name, f'{a.turn_count:,}', format_tokens(a.usage.total)]
        for name, a in sorted(result.by_project.items(), key=lambda x: -x[1].usage.total)[:top]
    ] if result.by_project else []

    transitions = activity_transitions(sessions, top_n=top)
    ramp = session_ramp_stats(sessions)

    signals = growth_signals(turns)
    stats = model_activity_breakdown(turns)
    eff = model_efficiency_signals(stats) if stats else []
    proj_breakdown = project_model_breakdown(turns) if stats else {}

    candidates = shell_automation_candidates(turns, min_count=3)
    edits = file_edit_frequency(turns, top_n=min(top, 5))
    verbs = prompt_action_verbs(turns, top_n=10)
    bigrams = prompt_bigrams(turns, top_n=10)

    # ── AI Insights (optional) ────────────────────────────────────────────────
    ai_html = ''
    if summarize_config:
        try:
            from .semantic import generate_ai_summary
            _ramp_stats = ramp
            context = {
                'period': f'{from_dt.date()} to {to_dt.date()}',
                'total_tokens': u.total,
                'total_turns': result.totals.turn_count,
                'cache_hit_pct': round(cache_pct, 1),
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
                    for s in stats[:5]
                ],
                'top_projects': [
                    {'project': name, 'turns': a.turn_count, 'total_tokens': a.usage.total}
                    for name, a in sorted(result.by_project.items(), key=lambda x: -x[1].usage.total)[:5]
                ],
                'growth_signals': [
                    {'project': s.project, 'kind': s.kind, 'description': s.description}
                    for s in signals
                ],
                'model_efficiency_signals': [
                    {'model': sig.model, 'kind': sig.kind, 'description': sig.description}
                    for sig in eff
                ],
                'shell_automation_candidates': [
                    {'command': c.command, 'count': c.count}
                    for c in candidates[:5]
                ],
                'prompt_verbs': [{'verb': v, 'count': c} for v, c in verbs],
                'session_ramp_mean': round(_ramp_stats.mean, 1),
                'session_ramp_p90': round(_ramp_stats.p90, 0),
                'session_count': _ramp_stats.session_count,
            }
            ai_text = generate_ai_summary(context, summarize_config, force=force_summary)
            if ai_text:
                import re
                # convert markdown headings and bold to HTML
                ai_safe = _esc(ai_text)
                ai_safe = re.sub(r'### (.+)', r'<h4>\1</h4>', ai_safe)
                ai_safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', ai_safe)
                ai_safe = re.sub(r'\n\n', '</p><p>', ai_safe)
                ai_safe = re.sub(r'\n(\d+\.\s)', r'</p><ol start="1"><li>', ai_safe)
                ai_safe = re.sub(r'\n', '<br>', ai_safe)
                ai_html = f'<div class="ai-body"><p>{ai_safe}</p></div>'
        except Exception as e:
            import sys
            print(f'[token-burn] AI Insights error: {e!r}', file=sys.stderr)

    # ── Intent Clusters (optional) ────────────────────────────────────────────
    clusters_html = ''
    try:
        from .semantic import _MODEL, analyze, label_cluster
        prompt_count = sum(1 for t in turns if len(t.user_text.strip().split()) >= 3)
        if prompt_count >= 4:
            examples_map, counts_map, k_used = analyze(turns)
            if examples_map:
                cluster_cards = []
                for cluster_id, exs in examples_map.items():
                    count = counts_map[cluster_id]
                    pct = count / prompt_count * 100 if prompt_count else 0
                    lbl = ''
                    if labels_config:
                        result_lbl = label_cluster(exs, labels_config)
                        if result_lbl:
                            lbl = f' — {_esc(result_lbl)}'
                    examples_li = ''.join(
                        f'<li>{_esc((ex[:120] + "…") if len(ex) > 120 else ex)}</li>'
                        for ex in exs[:3]
                    )
                    cluster_cards.append(
                        f'<div class="cluster-card">'
                        f'<div class="cluster-header">'
                        f'<span class="cluster-num">Cluster {cluster_id + 1}{lbl}</span>'
                        f'<span class="cluster-badge">{count} prompts · {pct:.0f}%</span>'
                        f'</div>'
                        f'<ul class="cluster-examples">{examples_li}</ul>'
                        f'</div>'
                    )
                clusters_html = (
                    f'<p class="meta">{prompt_count} prompts · k={k_used} · {_esc(_MODEL)}</p>'
                    f'<div class="cluster-grid">{"".join(cluster_cards)}</div>'
                )
    except ModuleNotFoundError:
        pass

    # ── chart data for model breakdown ────────────────────────────────────────
    chart_data = _chart_data_json(stats) if stats else '[]'
    activity_colors_js = json.dumps(_ACTIVITY_COLORS)

    # ── build model efficiency table rows ─────────────────────────────────────
    me_rows_html = ''
    if stats:
        for s in stats[:top]:
            acts = s.top_activities(13)
            bar = _activities_bar(acts)
            act_labels = ', '.join(f'{a} {p*100:.0f}%' for a, p in acts)
            me_rows_html += (
                f'<tr>'
                f'<td>{_esc(s.model)}</td>'
                f'<td class="num">{s.total_turns:,}</td>'
                f'<td class="num">{format_tokens(s.total_tokens)}</td>'
                f'<td class="num">{format_tokens(int(s.avg_tokens))}</td>'
                f'<td><div title="{_esc(act_labels)}">{bar}</div></td>'
                f'</tr>'
            )

    # ── project model breakdown rows ──────────────────────────────────────────
    pb_rows_html = ''
    for proj, proj_stats in proj_breakdown.items():
        for i, s in enumerate(proj_stats):
            acts = s.top_activities(13)
            bar = _activities_bar(acts)
            act_labels = ', '.join(f'{a} {p*100:.0f}%' for a, p in acts)
            proj_cell = f'<td class="proj-name">{_esc(proj)}</td>' if i == 0 else '<td></td>'
            pb_rows_html += (
                f'<tr>'
                f'{proj_cell}'
                f'<td>{_esc(s.model)}</td>'
                f'<td class="num">{s.total_turns:,}</td>'
                f'<td class="num">{format_tokens(s.total_tokens)}</td>'
                f'<td class="num">{format_tokens(int(s.avg_tokens))}</td>'
                f'<td><div title="{_esc(act_labels)}">{bar}</div></td>'
                f'</tr>'
            )

    # ── project token bars for chart ─────────────────────────────────────────
    proj_chart_data = json.dumps([
        {'name': name, 'tokens': a.usage.total, 'turns': a.turn_count}
        for name, a in sorted(result.by_project.items(), key=lambda x: -x[1].usage.total)[:top]
    ]) if result.by_project else '[]'

    # ── workflow transition rows ───────────────────────────────────────────────
    tr_rows_html = ''
    for t in transitions:
        tr_rows_html += (
            f'<tr>'
            f'<td><span class="act-chip" style="background:{_activity_color(t.from_activity)}">'
            f'{_esc(t.from_activity)}</span></td>'
            f'<td class="arrow">→</td>'
            f'<td><span class="act-chip" style="background:{_activity_color(t.to_activity)}">'
            f'{_esc(t.to_activity)}</span></td>'
            f'<td class="num">{t.count}</td>'
            f'<td class="num">{t.pct:.0%}</td>'
            f'</tr>'
        )

    return _TEMPLATE.format(
        period_label=_esc(period_label),
        from_date=_esc(str(from_dt.date())),
        to_date=_esc(str(to_dt.date())),
        generated=_esc(now),
        total_tokens=_esc(format_tokens(u.total)),
        total_tokens_raw=u.total,
        total_turns=f'{result.totals.turn_count:,}',
        cache_pct=f'{cache_pct:.1f}%',
        model_table=_html_table(['Model', 'Turns', 'Tokens', 'Avg/turn'], model_rows, 'model-summary-table') if model_rows else '',
        proj_table=_html_table(['Project', 'Turns', 'Tokens'], proj_rows, 'proj-table') if proj_rows else '',
        tr_rows_html=tr_rows_html,
        ramp_mean=f'{ramp.mean:.1f}',
        ramp_p90=f'{ramp.p90:.0f}',
        ramp_sessions=str(ramp.session_count),
        signals_table=_html_table(
            ['Project', 'Signal', 'Detail'],
            [[s.project, s.kind.replace('_', ' '), s.description] for s in signals],
            'signals-table',
        ) if signals else '<p class="empty">No signals flagged.</p>',
        me_rows_html=me_rows_html,
        eff_table=_html_table(
            ['Model', 'Signal', 'Detail'],
            [[sig.model, sig.kind.replace('_', ' '), sig.description] for sig in eff],
            'eff-signals-table',
        ) if eff else '',
        pb_rows_html=pb_rows_html,
        shell_table=_html_table(
            ['Command', 'Runs', 'Projects'],
            [[c.command, str(c.count), ', '.join(c.projects[:2])] for c in candidates[:5]],
            'shell-table',
        ) if candidates else '<p class="empty">No repeated shell commands.</p>',
        edits_table=_html_table(
            ['File', 'Edits'],
            [[f, str(c)] for f, c in edits],
            'edits-table',
        ) if edits else '',
        verbs_table=_html_table(
            ['Verb', 'Count'],
            [[v, str(c)] for v, c in verbs],
            'verbs-table',
        ) if verbs else '',
        bigrams_table=_html_table(
            ['Bigram', 'Count'],
            [[b, str(c)] for b, c in bigrams],
            'bigrams-table',
        ) if bigrams else '',
        clusters_html=clusters_html,
        ai_html=ai_html,
        chart_data=chart_data,
        activity_colors_js=activity_colors_js,
        proj_chart_data=proj_chart_data,
        tool_label=_esc(tool_label),
    )


_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>token-burn · {tool_label} · {period_label} · {from_date} to {to_date}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js" integrity="sha384-DhxhYObIMeMNGyAG7iK11OHzBIKyEIeRL0ad1iFPAOwZB8iirUlTT0O/WJJUk8+o" crossorigin="anonymous"></script>
<style>
:root {{
  --bg: #0f1117;
  --bg2: #1a1d27;
  --bg3: #22263a;
  --border: #2e3250;
  --text: #e2e8f0;
  --muted: #7c85a2;
  --accent: #6366f1;
  --accent2: #06b6d4;
  --green: #10b981;
  --yellow: #f59e0b;
  --red: #ef4444;
  --radius: 10px;
  --shadow: 0 2px 12px rgba(0,0,0,.4);
}}
[data-theme="light"] {{
  --bg: #f8fafc;
  --bg2: #ffffff;
  --bg3: #f1f5f9;
  --border: #e2e8f0;
  --text: #1e293b;
  --muted: #64748b;
  --accent: #4f46e5;
  --accent2: #0891b2;
  --shadow: 0 2px 12px rgba(0,0,0,.08);
}}
*,*::before,*::after {{box-sizing:border-box;margin:0;padding:0}}
html {{scroll-behavior:smooth}}
body {{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;display:flex;min-height:100vh}}

/* ── sidebar ── */
#sidebar {{
  position:fixed;top:0;left:0;bottom:0;width:220px;background:var(--bg2);
  border-right:1px solid var(--border);padding:24px 0;overflow-y:auto;
  z-index:100;display:flex;flex-direction:column;gap:2px;
}}
.sidebar-logo {{padding:0 20px 20px;font-weight:700;font-size:1.05rem;color:var(--accent);border-bottom:1px solid var(--border);margin-bottom:8px}}
.sidebar-logo span {{color:var(--muted);font-weight:400;font-size:.8rem;display:block}}
.nav-item {{
  display:block;padding:8px 20px;color:var(--muted);text-decoration:none;
  font-size:.85rem;border-left:3px solid transparent;transition:.15s;
}}
.nav-item:hover,.nav-item.active {{color:var(--text);border-left-color:var(--accent);background:var(--bg3)}}
.nav-section {{padding:14px 20px 4px;font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}
#theme-btn {{
  margin-top:auto;margin-left:20px;margin-right:20px;margin-bottom:4px;
  padding:7px 14px;border-radius:6px;border:1px solid var(--border);
  background:var(--bg3);color:var(--text);cursor:pointer;font-size:.8rem;
}}

/* ── main ── */
#main {{margin-left:220px;padding:40px 48px;max-width:1100px;width:100%}}
.page-header {{margin-bottom:40px}}
.page-header h1 {{font-size:1.6rem;font-weight:700;color:var(--text)}}
.page-header .meta {{color:var(--muted);font-size:.85rem;margin-top:4px}}

/* ── stat cards ── */
.stat-grid {{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px}}
.stat-card {{
  background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);
  padding:20px 24px;box-shadow:var(--shadow);
}}
.stat-card .label {{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}}
.stat-card .value {{font-size:2rem;font-weight:700;color:var(--text)}}
.stat-card .sub {{font-size:.8rem;color:var(--muted);margin-top:4px}}

/* ── sections ── */
.section {{margin-bottom:48px}}
.section-title {{
  font-size:1.1rem;font-weight:600;color:var(--text);
  padding-bottom:10px;border-bottom:1px solid var(--border);margin-bottom:20px;
  display:flex;align-items:center;gap:8px;
}}
.section-title .icon {{font-size:1.1rem}}
.subsection {{margin-top:28px}}
.subsection-title {{font-size:.9rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px}}

/* ── tables ── */
.data-table {{width:100%;border-collapse:collapse;font-size:.85rem}}
.data-table th {{
  padding:9px 12px;text-align:left;color:var(--muted);font-weight:600;
  font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;
  border-bottom:2px solid var(--border);white-space:nowrap;cursor:pointer;user-select:none;
}}
.data-table th:hover {{color:var(--text)}}
.sort-icon {{margin-left:4px;opacity:.4;font-size:.8rem}}
.data-table th.sort-asc .sort-icon::after {{content:"↑";opacity:1}}
.data-table th.sort-desc .sort-icon::after {{content:"↓";opacity:1}}
.data-table th.sort-asc .sort-icon, .data-table th.sort-desc .sort-icon {{opacity:1}}
.data-table td {{padding:9px 12px;border-bottom:1px solid var(--border)}}
.data-table tr:last-child td {{border-bottom:none}}
.data-table tr:hover td {{background:var(--bg3)}}
.data-table .num {{text-align:right;font-variant-numeric:tabular-nums}}

/* ── activity stack bar ── */
.act-stack {{display:flex;height:14px;border-radius:4px;overflow:hidden;min-width:120px;background:var(--bg3)}}
.act-bar {{height:100%;transition:.2s}}

/* ── activity chip ── */
.act-chip {{padding:2px 8px;border-radius:4px;font-size:.78rem;color:#fff;font-weight:500}}
.arrow {{color:var(--muted);text-align:center}}

/* ── charts ── */
.chart-wrap {{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}}
.chart-grid {{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}}
@media(max-width:800px){{.chart-grid{{grid-template-columns:1fr}}}}

/* ── cluster cards ── */
.cluster-grid {{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}}
.cluster-card {{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px}}
.cluster-header {{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}}
.cluster-num {{font-weight:600;font-size:.9rem}}
.cluster-badge {{background:var(--bg3);color:var(--muted);font-size:.75rem;padding:2px 8px;border-radius:12px}}
.cluster-examples {{list-style:none;padding:0}}
.cluster-examples li {{font-size:.82rem;color:var(--muted);padding:3px 0;border-bottom:1px solid var(--border);font-style:italic}}
.cluster-examples li:last-child {{border:none}}

/* ── ai insights ── */
.ai-body {{font-size:.9rem;line-height:1.8}}
.ai-body h4 {{font-size:.95rem;font-weight:600;margin:16px 0 6px;color:var(--accent)}}
.ai-body p {{margin-bottom:12px;color:var(--text)}}
.ai-body ol {{padding-left:20px;margin-bottom:12px}}
.ai-body li {{margin-bottom:8px}}
.ai-body strong {{color:var(--text)}}

/* ── misc ── */
.proj-name {{font-weight:500}}
.empty {{color:var(--muted);font-size:.85rem;padding:12px 0}}
.meta {{color:var(--muted);font-size:.8rem;margin-bottom:12px}}
.ramp-stats {{display:flex;gap:32px;padding:16px;background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);margin-top:16px}}
.ramp-stat .ramp-val {{font-size:1.6rem;font-weight:700}}
.ramp-stat .ramp-lbl {{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}}

.table-wrap {{overflow-x:auto}}
</style>
</head>
<body>

<nav id="sidebar">
  <div class="sidebar-logo">token-burn<span>{period_label} · {from_date}</span></div>
  <span class="nav-section">Overview</span>
  <a class="nav-item" href="#summary">Summary</a>
  <a class="nav-item" href="#projects">Projects</a>
  <span class="nav-section">Analysis</span>
  <a class="nav-item" href="#workflow">Workflow</a>
  <a class="nav-item" href="#growth">Growth Signals</a>
  <a class="nav-item" href="#model-efficiency">Model Efficiency</a>
  <span class="nav-section">Patterns</span>
  <a class="nav-item" href="#patterns">Shell &amp; Files</a>
  <a class="nav-item" href="#prompts">Prompt Patterns</a>
  <a class="nav-item" href="#clusters">Intent Clusters</a>
  <a class="nav-item" href="#ai-insights">AI Insights</a>
  <button id="theme-btn" onclick="toggleTheme()">☀ Light mode</button>
</nav>

<main id="main">
  <div class="page-header">
    <h1>token-burn report — {tool_label} · {period_label}</h1>
    <div class="meta">{from_date} → {to_date} · Generated {generated}</div>
  </div>

  <!-- ── Summary ── -->
  <section id="summary" class="section">
    <div class="section-title"><span class="icon">📊</span>Summary</div>
    <div class="stat-grid">
      <div class="stat-card">
        <div class="label">Total Tokens</div>
        <div class="value">{total_tokens}</div>
      </div>
      <div class="stat-card">
        <div class="label">Total Turns</div>
        <div class="value">{total_turns}</div>
      </div>
      <div class="stat-card">
        <div class="label">Cache Hit Rate</div>
        <div class="value" style="color:var(--green)">{cache_pct}</div>
      </div>
    </div>
    <div class="table-wrap">{model_table}</div>
  </section>

  <!-- ── Projects ── -->
  <section id="projects" class="section">
    <div class="section-title"><span class="icon">📁</span>Projects</div>
    <div class="chart-grid">
      <div class="chart-wrap"><canvas id="projTokenChart" height="240"></canvas></div>
      <div class="chart-wrap"><canvas id="projTurnChart" height="240"></canvas></div>
    </div>
    <div class="table-wrap">{proj_table}</div>
  </section>

  <!-- ── Workflow ── -->
  <section id="workflow" class="section">
    <div class="section-title"><span class="icon">🔀</span>Workflow</div>
    <div class="table-wrap">
      <table class="data-table">
        <thead><tr><th>From</th><th></th><th>To</th><th class="num">Count</th><th class="num">%</th></tr></thead>
        <tbody>{tr_rows_html}</tbody>
      </table>
    </div>
    <div class="ramp-stats">
      <div class="ramp-stat"><div class="ramp-val">{ramp_mean}</div><div class="ramp-lbl">Mean turns to first edit</div></div>
      <div class="ramp-stat"><div class="ramp-val">{ramp_p90}</div><div class="ramp-lbl">P90 turns</div></div>
      <div class="ramp-stat"><div class="ramp-val">{ramp_sessions}</div><div class="ramp-lbl">Sessions</div></div>
    </div>
  </section>

  <!-- ── Growth Signals ── -->
  <section id="growth" class="section">
    <div class="section-title"><span class="icon">📈</span>Growth Signals</div>
    <div class="table-wrap">{signals_table}</div>
  </section>

  <!-- ── Model Efficiency ── -->
  <section id="model-efficiency" class="section">
    <div class="section-title"><span class="icon">🤖</span>Model Efficiency</div>
    <div class="chart-grid">
      <div class="chart-wrap"><canvas id="modelActivityChart" height="240"></canvas></div>
      <div class="chart-wrap"><canvas id="modelTokenChart" height="240"></canvas></div>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead><tr><th>Model</th><th class="num">Turns</th><th class="num">Tokens</th><th class="num">Avg/turn</th><th>Activities</th></tr></thead>
        <tbody>{me_rows_html}</tbody>
      </table>
    </div>
    {eff_table}
    <div class="subsection">
      <div class="subsection-title">By Project</div>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Project</th><th>Model</th><th class="num">Turns</th><th class="num">Tokens</th><th class="num">Avg/turn</th><th>Activities</th></tr></thead>
          <tbody>{pb_rows_html}</tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ── Patterns ── -->
  <section id="patterns" class="section">
    <div class="section-title"><span class="icon">⚡</span>Patterns — Shell &amp; Files</div>
    <div class="subsection-title">Top Shell Commands</div>
    <div class="table-wrap">{shell_table}</div>
    <div class="subsection" style="margin-top:24px">
      <div class="subsection-title">Hottest Files</div>
      <div class="table-wrap">{edits_table}</div>
    </div>
  </section>

  <!-- ── Prompt Patterns ── -->
  <section id="prompts" class="section">
    <div class="section-title"><span class="icon">💬</span>Prompt Patterns</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <div>
        <div class="subsection-title">Verbs</div>
        <div class="table-wrap">{verbs_table}</div>
      </div>
      <div>
        <div class="subsection-title">Bigrams</div>
        <div class="table-wrap">{bigrams_table}</div>
      </div>
    </div>
  </section>

  <!-- ── Intent Clusters ── -->
  <section id="clusters" class="section">
    <div class="section-title"><span class="icon">🧩</span>Intent Clusters</div>
    {clusters_html}
  </section>

  <!-- ── AI Insights ── -->
  <section id="ai-insights" class="section">
    <div class="section-title"><span class="icon">✨</span>AI Insights</div>
    {ai_html}
  </section>

</main>

<script>
const CHART_DATA = {chart_data};
const ACTIVITY_COLORS = {activity_colors_js};
const PROJ_DATA = {proj_chart_data};
const DEFAULT_COLOR = '#94a3b8';

function actColor(name) {{
  return ACTIVITY_COLORS[name] || DEFAULT_COLOR;
}}

function isDark() {{
  return document.documentElement.getAttribute('data-theme') !== 'light';
}}

function chartDefaults() {{
  const dark = isDark();
  return {{
    color: dark ? '#e2e8f0' : '#1e293b',
    gridColor: dark ? 'rgba(255,255,255,.07)' : 'rgba(0,0,0,.07)',
    bg: dark ? '#1a1d27' : '#ffffff',
  }};
}}

function buildProjCharts() {{
  const names = PROJ_DATA.map(d => d.name);
  const tokens = PROJ_DATA.map(d => d.tokens);
  const turns = PROJ_DATA.map(d => d.turns);
  const c = chartDefaults();

  new Chart(document.getElementById('projTokenChart'), {{
    type: 'bar',
    data: {{
      labels: names,
      datasets: [{{ label: 'Tokens', data: tokens, backgroundColor: '#6366f1', borderRadius: 4 }}],
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{ display: false }},
        title: {{ display: true, text: 'Tokens by Project', color: c.color }},
        tooltip: {{ callbacks: {{ label: ctx => ' ' + (ctx.raw / 1e6).toFixed(1) + 'M tokens' }} }},
      }},
      scales: {{
        x: {{ ticks: {{ color: c.color, maxRotation: 35 }}, grid: {{ color: c.gridColor }} }},
        y: {{ ticks: {{ color: c.color, callback: v => (v/1e6).toFixed(1)+'M' }}, grid: {{ color: c.gridColor }} }},
      }},
    }},
  }});

  new Chart(document.getElementById('projTurnChart'), {{
    type: 'bar',
    data: {{
      labels: names,
      datasets: [{{ label: 'Turns', data: turns, backgroundColor: '#06b6d4', borderRadius: 4 }}],
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{ display: false }},
        title: {{ display: true, text: 'Turns by Project', color: c.color }},
      }},
      scales: {{
        x: {{ ticks: {{ color: c.color, maxRotation: 35 }}, grid: {{ color: c.gridColor }} }},
        y: {{ ticks: {{ color: c.color }}, grid: {{ color: c.gridColor }} }},
      }},
    }},
  }});
}}

function buildModelCharts() {{
  if (!CHART_DATA.length) return;
  const c = chartDefaults();

  // stacked bar: activity breakdown per model
  const models = CHART_DATA.map(d => d.model);
  const allActs = [...new Set(CHART_DATA.flatMap(d => d.activities.map(a => a.name)))];
  const datasets = allActs.map(act => ({{
    label: act,
    data: CHART_DATA.map(d => {{
      const found = d.activities.find(a => a.name === act);
      return found ? found.pct : 0;
    }}),
    backgroundColor: actColor(act),
    borderRadius: 0,
  }}));

  new Chart(document.getElementById('modelActivityChart'), {{
    type: 'bar',
    data: {{ labels: models, datasets }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{ position: 'right', labels: {{ color: c.color, boxWidth: 12, font: {{ size: 11 }} }} }},
        title: {{ display: true, text: 'Activity Mix by Model', color: c.color }},
      }},
      scales: {{
        x: {{ stacked: true, ticks: {{ color: c.color }}, grid: {{ color: c.gridColor }} }},
        y: {{ stacked: true, max: 100, ticks: {{ color: c.color, callback: v => v+'%' }}, grid: {{ color: c.gridColor }} }},
      }},
    }},
  }});

  // horizontal bar: avg tokens per turn
  new Chart(document.getElementById('modelTokenChart'), {{
    type: 'bar',
    data: {{
      labels: models,
      datasets: [{{
        label: 'Avg tokens/turn',
        data: CHART_DATA.map(d => d.avg),
        backgroundColor: '#f59e0b',
        borderRadius: 4,
      }}],
    }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      plugins: {{
        legend: {{ display: false }},
        title: {{ display: true, text: 'Avg Tokens / Turn', color: c.color }},
        tooltip: {{ callbacks: {{ label: ctx => ' ' + (ctx.raw/1000).toFixed(1) + 'k' }} }},
      }},
      scales: {{
        x: {{ ticks: {{ color: c.color, callback: v => (v/1000).toFixed(0)+'k' }}, grid: {{ color: c.gridColor }} }},
        y: {{ ticks: {{ color: c.color }}, grid: {{ color: c.gridColor }} }},
      }},
    }},
  }});
}}

// ── sortable tables ──
document.querySelectorAll('table.sortable').forEach(tbl => {{
  const headers = tbl.querySelectorAll('th.sortable-header');
  headers.forEach((th, col) => {{
    let dir = 0;
    th.addEventListener('click', () => {{
      headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
      dir = dir === 1 ? -1 : 1;
      th.classList.add(dir === 1 ? 'sort-asc' : 'sort-desc');
      const tbody = tbl.querySelector('tbody');
      const rows = [...tbody.querySelectorAll('tr')];
      rows.sort((a, b) => {{
        const av = a.cells[col]?.textContent.trim() ?? '';
        const bv = b.cells[col]?.textContent.trim() ?? '';
        const an = parseFloat(av.replace(/[^0-9.\-]/g, ''));
        const bn = parseFloat(bv.replace(/[^0-9.\-]/g, ''));
        if (!isNaN(an) && !isNaN(bn)) return (an - bn) * dir;
        return av.localeCompare(bv) * dir;
      }});
      rows.forEach(r => tbody.appendChild(r));
    }});
  }});
}});

// ── active nav on scroll ──
const sections = document.querySelectorAll('section[id]');
const navItems = document.querySelectorAll('.nav-item');
const obs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{
      navItems.forEach(n => n.classList.toggle('active', n.getAttribute('href') === '#' + e.target.id));
    }}
  }});
}}, {{ threshold: 0.2 }});
sections.forEach(s => obs.observe(s));

// ── theme toggle ──
function toggleTheme() {{
  const root = document.documentElement;
  const btn = document.getElementById('theme-btn');
  if (root.getAttribute('data-theme') === 'light') {{
    root.removeAttribute('data-theme');
    btn.textContent = '☀ Light mode';
  }} else {{
    root.setAttribute('data-theme', 'light');
    btn.textContent = '🌙 Dark mode';
  }}
}}

buildProjCharts();
buildModelCharts();
</script>
</body>
</html>'''
