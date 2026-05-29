# claude-token-burn

CLI and TUI for tracking Claude Code token usage. Reads session transcripts directly from `~/.claude/projects/` — no API keys, no proxy, no wrapper.

## Install

```bash
pipx install claude-token-burn
```

Zero-install run:

```bash
uvx claude-token-burn
```

## Usage

```bash
claude-token-burn              # interactive TUI dashboard (default 7-day window)
claude-token-burn today        # today's tokens
claude-token-burn month        # this month's tokens
claude-token-burn report -p 30days
claude-token-burn report --from 2026-05-01 --to 2026-05-29
claude-token-burn report --refresh 60     # auto-refresh every 60s
claude-token-burn status                  # one-liner: today + month
claude-token-burn status --format json
claude-token-burn project                 # drill-down by project (interactive)
claude-token-burn project token-burn      # drill-down for a specific project
claude-token-burn export                  # CSV export (today / 7d / 30d)
claude-token-burn export -f json
```

## TUI

Launch with `claude-token-burn` (no arguments).

```
  Today    [ 7 Days ]   30 Days    Month

 claude-token-burn  7 Days
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
claude-token-burn project
```

Lists recent projects sorted by last active date. Enter a number to select or type a search term to filter. Displays token usage broken down by day, activity, tool, shell command, and MCP server for the selected project.

```bash
claude-token-burn project orchid -p 7days
claude-token-burn project myapp --from 2026-05-01 --to 2026-05-15
```

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

Turns are deduplicated by `message.id`. Date filtering is per-entry timestamp, so long sessions spanning midnight are bucketed correctly.

## Development

```bash
git clone https://github.com/agentseal/claude-token-burn
cd claude-token-burn
uv venv .venv --python 3.11
uv pip install -e .
pytest
claude-token-burn status
```

Requires Python 3.11+.
