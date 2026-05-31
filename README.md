# token-burn

CLI and TUI for tracking AI token usage and cost. Currently supports **Claude Code only** — reads session transcripts directly from `~/.claude/projects/` — no API keys, no proxy, no wrapper.

## Install

```bash
pipx install token-burn
```

Zero-install run:

```bash
uvx token-burn
```

Optional semantic clustering features:

```bash
pip install "token-burn[semantic]"
# adds: fastembed (~150MB), scikit-learn, numpy
# downloads on first use: BAAI/bge-small-en-v1.5 (~130MB, cached in ~/.cache/fastembed)
```

## Usage

```bash
token-burn              # interactive TUI dashboard (default 7-day window)
token-burn today        # today's tokens
token-burn month        # this month's tokens
token-burn report -p 30days
token-burn report --from 2026-05-01 --to 2026-05-29
token-burn report --refresh 60     # auto-refresh every 60s
token-burn status                  # one-liner: today + month
token-burn status --format json
token-burn project                 # drill-down by project (interactive)
token-burn project token-burn      # drill-down for a specific project
token-burn export                  # CSV export (today / 7d / 30d)
token-burn export -f json

token-burn patterns                # shell automation candidates + hottest files + user prompt patterns
token-burn workflow                # activity transition sequences + session ramp time
token-burn growth                  # per-project efficiency gaps
token-burn semantic                # intent clustering of user prompts (requires [semantic] extra)
```

## TUI

Launch with `token-burn` (no arguments).

```
  Today    [ 7 Days ]   30 Days    Month

 token-burn  7 Days
    92.4M total   1,330 turns   96.1% cache hit
    5.9k in   896.6k out   89.3M cached   2.3M written

 ┌─ Daily Activity ──┐  ┌─ By Project ──────┐
 │ ████▁▁ 2026-05-23 │  │ ████ token-burn   │
 │ ███▁▁▁ 2026-05-24 │  │ ██▁▁ orchid       │
 │ ...               │  │ ...               │
 └───────────────────┘  └───────────────────┘

 ┌─ By Activity ─────┐  ┌─ By Model ────────┐
 │ Coding            │  │ Sonnet 4.6        │
 │ Exploration       │  │ Haiku 4.5         │
 │ ...               │  │ ...               │
 └───────────────────┘  └───────────────────┘
```

**Keyboard shortcuts:**

| Key | Action |
|-----|--------|
| `←` / `→` | Cycle periods |
| `1` | Today |
| `2` | 7 Days |
| `3` | 30 Days |
| `4` | Month |
| `r` | Refresh |
| `q` | Quit |

## Project drill-down

```bash
token-burn project
```

Lists recent projects sorted by last active date. Enter a number to select or type a search term to filter. Displays token usage broken down by day, activity, tool, shell command, and MCP server for the selected project.

```bash
token-burn project orchid -p 7days
token-burn project myapp --from 2026-05-01 --to 2026-05-15
```

## Workflow analysis

### patterns

Shell automation candidates, hottest edited files, and user prompt patterns.

```bash
token-burn patterns              # 30-day default
token-burn patterns -p 7days
token-burn patterns --min 5      # raise repetition threshold (default 3)
```

Shows:
- **Claude's top Bash operations** — commands Claude ran most often on your behalf, normalized to first two words
- **Hottest files** — files edited most frequently across sessions
- **User prompt verbs** — leading action words from your typed prompts
- **User prompt bigrams** — top word pairs (stopwords removed)
- **Repeated prompts** — exact prompts typed more than once

### workflow

Activity transition sequences and session ramp time.

```bash
token-burn workflow
token-burn workflow -p 7days
```

Shows the most common activity-to-activity transitions across sessions (self-loops excluded) and how many turns elapse before the first file edit per session (mean + p90).

### growth

Per-project efficiency signals based on activity ratios.

```bash
token-burn growth
token-burn growth -p 30days
```

Flags: high debug-to-test ratio (low test coverage signal), zero test activity alongside repeated debugging, and high conversation ratio (planning or requirements overhead).

## Semantic clustering

Requires `pip install "token-burn[semantic]"`.

```bash
token-burn semantic              # 30-day default, k auto-selected
token-burn semantic -p 90days    # longer window = better clusters
token-burn semantic -k 10        # override cluster count
token-burn semantic --project orchid
```

Embeds all user prompts with `fastembed` (`BAAI/bge-small-en-v1.5`), clusters with k-means, and shows the three nearest-to-centroid real prompts per cluster. `k` defaults to `sqrt(n/2)` capped at 20. Embeddings are cached in `~/.cache/token-burn/embeddings.npz` and reused on subsequent runs.

## Token breakdowns

All reports show four token types plus total:

| Type | Description |
|------|-------------|
| Input | Tokens not served from cache |
| Output | Generated tokens |
| Cache read | Tokens read from prompt cache |
| Cache write | Tokens written to prompt cache |

Grouped by: day, project, model, activity, tool, shell command, MCP server.

## Activity categories

Each turn is classified into one of 13 categories:

| Category | Trigger |
|----------|---------|
| Coding | `Edit` or `Write` tool used |
| Feature Dev | add/create/implement keywords + edits |
| Refactoring | refactor/rename/simplify + edits |
| Debugging | error/fix/bug keywords + tool use |
| Testing | pytest/jest/go test in Bash |
| Exploration | Read/Grep/Glob/WebSearch only |
| Planning | EnterPlanMode / TaskCreate tools |
| Delegation | Agent / Task tool spawn |
| Git Ops | git push/commit/merge in Bash |
| Build/Deploy | docker/npm build/pip install in Bash |
| Brainstorming | brainstorm/design keywords, no edits |
| Conversation | No tools, pure text |
| General | Skill tool or uncategorized |

## Data sources

- `~/.claude/projects/<sanitized-cwd>/<session-id>.jsonl`
- Override base path with `CLAUDE_CONFIG_DIR` env var
- macOS: `~/Library/Application Support/Claude/local-agent-mode-sessions/`

Turns are deduplicated by `message.id`. Date filtering is per-entry timestamp, so long sessions spanning midnight are bucketed correctly. Skill body injections, task notifications, and system XML blocks are stripped from user text before analysis.

## Development

```bash
git clone https://github.com/agentseal/token-burn
cd token-burn
uv venv .venv --python 3.11
uv pip install -e .
pytest
token-burn status
```

Optional extras for semantic clustering:

```bash
uv pip install -e ".[semantic]"
token-burn semantic
```

Requires Python 3.11+.
