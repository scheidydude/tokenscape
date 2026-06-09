# hindsight

CLI and TUI for tracking AI token usage and cost — and for understanding how you actually work. Reads session transcripts directly from disk — no API keys, no proxy, no wrapper. Supports **Claude Code** and **Codex CLI**.

## Install

```bash
pipx install hindsight
```

Zero-install run:

```bash
uvx hindsight
```

Optional semantic clustering:

```bash
pip install "hindsight[semantic]"
# adds: fastembed (~150MB), scikit-learn, numpy
# downloads on first use: BAAI/bge-small-en-v1.5 (~130MB, cached in ~/.cache/fastembed)
```

## Tool selection

By default, hindsight reads Claude Code sessions. Pass `--tool codex` to analyze Codex CLI sessions instead. The flag applies to all commands and the TUI.

```bash
hindsight --tool codex today
hindsight --tool codex report -p 30days
hindsight --tool codex full-report --html-output report.html
hindsight --tool codex          # TUI in Codex mode
```

| Tool | Session path |
|------|-------------|
| `claude` (default) | `~/.claude/projects/` + `~/Library/Application Support/Claude/local-agent-mode-sessions/` |
| `codex` | `~/.codex/sessions/` |

## Usage

```bash
hindsight              # interactive TUI dashboard (default 7-day window)
hindsight today        # today's tokens
hindsight month        # this month's tokens
hindsight report -p 30days
hindsight report --from 2026-05-01 --to 2026-05-29
hindsight report --refresh 60     # auto-refresh every 60s
hindsight status                  # one-liner: today + month
hindsight status --format json
hindsight project                 # drill-down by project (interactive)
hindsight project myproject      # drill-down for a specific project
hindsight export                  # CSV export (today / 7d / 30d)
hindsight export -f json

hindsight bundle                  # create a zip of session data to share with teammates
hindsight full-report             # full markdown report to stdout (all commands in one pass)
hindsight full-report --source teammate-bundle-20260531.zip
hindsight full-report --top 10 --output report.md
hindsight full-report --html-output report.html        # interactive HTML report
hindsight full-report --output report.md --html-output report.html  # both at once
hindsight full-report --summarize --output report.md   # append AI Insights section via LLM
hindsight full-report --summarize --force-new          # bypass cached summary
hindsight patterns                # shell automation candidates + hottest files + user prompt patterns
hindsight workflow                # activity transition sequences + session ramp time
hindsight growth                  # per-project efficiency gaps
hindsight models                  # model usage breakdown by activity + efficiency signals
hindsight semantic                # intent clustering of user prompts (requires [semantic] extra)
```

## TUI

Launch with `hindsight` (no arguments).

```
  Today    [ 7 Days ]   30 Days    Month

 hindsight  [CLAUDE]  7 Days
    92.4M total   1,330 turns   96.1% cache hit
    5.9k in   896.6k out   89.3M cached   2.3M written

 ┌─ Daily Activity ──┐  ┌─ By Project ──────┐
 │ ████▁▁ 2026-05-23 │  │ ████ hindsight   │
 │ ███▁▁▁ 2026-05-24 │  │ ██▁▁ orchid       │
 │ ...               │  │ ...               │
 └───────────────────┘  └───────────────────┘

 ┌─ By Activity ─────┐  ┌─ By Model ────────┐
 │ Coding            │  │ Sonnet 4.6        │
 │ Exploration       │  │ Haiku 4.5         │
 │ ...               │  │ ...               │
 └───────────────────┘  └───────────────────┘

 ┌─ Workflow Transitions ────────────────────┐  ┌─ Growth Signals ──────────────────────────┐
 │ ████ Coding       → Debugging   47  18%  │  │ ! hindsight  debug/test ratio  4.2× ...  │
 │ ███  Debugging    → Coding      38  15%  │  │ ! orchid      conversation      62% ...   │
 │ ...                                      │  │                                           │
 │   ramp  mean 3.1  p90 11  (42 sessions)  │  │                                           │
 └──────────────────────────────────────────┘  └───────────────────────────────────────────┘
```

**Keyboard shortcuts:**

| Key | Action |
|-----|--------|
| `←` / `→` | Cycle periods |
| `1` | Today |
| `2` | 7 Days |
| `3` | 30 Days |
| `4` | Month |
| `t` | Toggle tool (CLAUDE ↔ CODEX) |
| `r` | Refresh |
| `q` | Quit |

The active tool is shown in the header as `[CLAUDE]` (blue) or `[CODEX]` (green). Switching with `t` reloads all panels immediately.

## Project drill-down

```bash
hindsight project
```

Lists recent projects sorted by last active date. Enter a number to select or type a search term to filter. Displays token usage broken down by day, activity, tool, shell command, and MCP server for the selected project.

```bash
hindsight project orchid -p 7days
hindsight project myapp --from 2026-05-01 --to 2026-05-15
```

---

## Workflow analysis

Beyond token cost, these commands answer: *what do you repeatedly ask Claude to do, where do you spend the most time, and what does that reveal about your workflow?*

| Command | Question answered | Time to run |
|---------|-------------------|-------------|
| `patterns` | What repeats at the mechanical level? | < 2s |
| `workflow` | How do sessions actually flow? | < 2s |
| `growth` | Which projects have process gaps? | < 2s |
| `models` | Which models do what, and is that efficient? | < 2s |
| `semantic` | What are my real recurring intents? | 5–30s first run, < 2s cached |
| `full-report` | All of the above as a single markdown document | < 5s (+ semantic if installed) |
| `full-report --html-output` | All of the above as an interactive HTML report | < 5s (+ semantic if installed) |
| `full-report --summarize` | All of the above + AI-generated insights section | depends on LLM |

A useful sequence: run `semantic` to find your top intent clusters, cross-reference with `patterns` to see the mechanical steps that accompany them, check `growth` for coverage or documentation gaps in those projects, and use `workflow` to see where in a session those patterns tend to occur.

### patterns

**What it answers:** *What does Claude do for me repeatedly, and what do I keep asking for?*

```bash
hindsight patterns              # 30-day default
hindsight patterns -p 7days
hindsight patterns --min 5      # raise repetition threshold (default 3)
```

**Claude's top Bash operations** — Every time Claude runs a shell command on your behalf, it's recorded. `patterns` counts these, normalized to the first two words, and surfaces the ones that repeat most. A command Claude runs 20+ times is a candidate for an alias, a Makefile target, or a CLAUDE.md shortcut so Claude stops reinventing it every session. High counts signal that Claude is doing the same mechanical step repeatedly — a sign the step could be encoded as a convention rather than re-derived each time.

**Hottest files** — Files Claude edits most frequently across sessions. A file appearing 15 times in 30 days is either a core module (expected) or a chronic trouble spot. Cross-reference with `growth`: if the same file appears in both hottest-files and your debug-heavy projects, it may warrant refactoring or better test coverage.

**User prompt verbs, bigrams, and repeated prompts** — These sections analyze what *you* typed, not what Claude ran. The leading verb of each prompt shows your dominant intent: `add`, `fix`, `update`, `check`. Bigrams surface recurring topic pairs after stopwords are removed. Exact repeated prompts are the highest-value automation targets — if you typed the same thing four times, it belongs in a slash command or CLAUDE.md workflow.

### workflow

**What it answers:** *How does my work actually flow within a session, and how long does it take me to get to productive work?*

```bash
hindsight workflow
hindsight workflow -p 30days
```

**Activity transitions** — Each turn is classified into one of 13 activity types (Coding, Debugging, Exploration, Planning, etc.). `workflow` counts transitions between activities across all sessions. A high `Exploration → Coding` rate means you typically read before you write. A high `Coding → Debugging` rate means edits often need follow-up correction. These aren't judgements — they're a map of your actual process, which is the first step to changing it intentionally. Self-transitions are excluded; only cross-activity moves are shown.

**Session ramp time** — For each session, this counts how many turns elapsed before the first file edit. The mean and p90 tell you how much discovery and conversation overhead precedes actual changes. A high mean (10+ turns) may indicate that context being re-derived from scratch each session could instead be pre-loaded via CLAUDE.md or project documentation.

### growth

**What it answers:** *Where are the gaps in my process, by project?*

```bash
hindsight growth
hindsight growth -p 30days
```

**Debug-to-test ratio** — Compares turns classified as `Debugging` against turns classified as `Testing` within each project. A ratio above 3×, or zero test turns alongside repeated debugging, flags a project where bugs are being found reactively rather than caught proactively. This doesn't tell you how to add tests — it tells you which project most needs them.

**Conversation ratio** — The fraction of turns that are pure conversation (no tools used). High conversation is normal for design and review, but a project staying above 40% across many sessions often means unclear requirements regenerating the same discussion, missing documentation being reconstructed repeatedly, or architectural uncertainty that hasn't been resolved. Projects with fewer than five turns in the period are excluded to avoid noise.

### models

**What it answers:** *Which models are being used for what, and is that a good match?*

```bash
hindsight models
hindsight models -p 7days
hindsight models --by-project     # add per-project model breakdown
```

**Model × activity breakdown** — For each model in the period, shows total turns, total tokens, average tokens per turn, and the top three activity categories by share of turns. A model averaging 2k tokens/turn on Conversation is a different story than one averaging 80k tokens/turn on Feature Dev.

**Efficiency signals** — Flags any model where more than 30% of its turns fell into low-value activity categories (Conversation, Git Ops, General, Delegation). This isn't always actionable (Claude Code picks the model, not you), but it surfaces patterns worth knowing — e.g. Opus spending most of its turns on pure conversation turns that Sonnet handles equally well.

**By project (`--by-project`)** — Adds a second table showing model usage broken down per project: which model each project used, how many turns, total tokens, and top two activities. Useful for spotting a project that consistently pulls in a more expensive model than others.

### semantic

**What it answers:** *What are the 6–10 recurring things I actually ask Claude to do?*

Requires `pip install "hindsight[semantic]"`.

```bash
hindsight semantic              # 90-day default, k auto-selected
hindsight semantic -p 90days    # longer window = better clusters
hindsight semantic -k 10        # override cluster count
hindsight semantic --project orchid
hindsight semantic --labels     # generate 2-3 word labels via LLM (see below)
```

`patterns` can tell you that you typed `add` 12 times and `fix` 8 times, but `add a search endpoint`, `add rate limiting`, and `add pagination` are three instances of the same intent — pure counting sees them as unrelated. `semantic` embeds every prompt you typed using a local neural model and groups them by meaning, not wording.

Each prompt is embedded with `fastembed` using `BAAI/bge-small-en-v1.5` (33M parameters, ~130MB, fully offline). Embeddings are cached in `~/.cache/hindsight/embeddings.npz` so re-runs are fast. Clusters are computed with k-means; `k` is auto-selected as `sqrt(n/2)` capped at 20. Each cluster is represented by its three nearest-to-centroid real prompts — you see your own words, not a generated label.

Prompts under three words are excluded (they're confirmations, not intent). A large cluster (20%+ of prompts) mapping to a single task type is an automation candidate: a slash command, a CLAUDE.md workflow entry, or a custom tool. A cluster of documentation prompts that follows feature work suggests a step that could be triggered automatically.

**LLM cluster labels (`--labels`)** — Pass `--labels` to generate a 2–3 word label per cluster instead of inferring the theme from examples. Requires a config file at `~/.config/hindsight/config.toml` (respects `XDG_CONFIG_HOME`). Supports any OpenAI-compatible endpoint:

```toml
[provider]
base_url = "http://localhost:11434/v1"   # Ollama (non-thinking models only)
api_key  = "ollama"
model    = "llama3.2:latest"

# llama.cpp (recommended for thinking models — qwen3, deepseek-r1, etc.):
# base_url = "http://your-server/v1"
# api_key  = "none"
# model    = "Qwen3.6-35B-A3B-MXFP4_MOE.gguf"

# Anthropic:
# base_url = "https://api.anthropic.com/v1"
# api_key  = "sk-ant-..."
# model    = "claude-haiku-4-5-20251001"

# LM Studio / OpenRouter — any /v1/chat/completions endpoint
```

Labels are cached in `~/.cache/hindsight/labels.json` keyed by cluster content, so repeat runs with stable clusters make no API calls. If the config is absent or the API call fails, `--labels` silently falls back to showing example prompts.

### full-report

**What it answers:** *Everything, in one document.*

```bash
hindsight full-report                        # 30-day default, stdout
hindsight full-report -p 7days               # shorter window
hindsight full-report --top 12               # more rows per table (default 8)
hindsight full-report --labels               # LLM cluster labels (requires config)
hindsight full-report --output report.md     # write markdown to file
hindsight full-report --html-output report.html             # write interactive HTML report
hindsight full-report --output report.md --html-output report.html  # both at once
hindsight full-report --summarize            # append AI Insights section (requires config)
hindsight full-report --summarize --force-new  # bypass cached summary
```

Runs all analysis in a single pass. Emits a markdown document (or interactive HTML report, or both) covering: summary, projects, workflow transitions + session ramp, growth signals, model efficiency + by-project model breakdown, patterns (shell commands, hottest files, prompt verbs, bigrams), and intent clusters if `[semantic]` is installed. Status/warning messages go to stderr so `hindsight full-report > report.md` works cleanly.

**HTML report (`--html-output`)** — Generates a self-contained interactive HTML file alongside (or instead of) the markdown report. Includes all the same sections rendered with sortable tables, stacked activity-bar charts, and Chart.js bar charts for project token/turn breakdowns and model activity mix. Features a collapsible sidebar with scroll-aware navigation and a dark/light mode toggle. No server required — open the file directly in any browser.

**AI Insights (`--summarize`)** — Appends a `## AI Insights` section written by an LLM, covering four areas: usage patterns, token efficiency, model selection, and recommended actions. The LLM receives a structured JSON summary of the report data (no raw prompts) and responds with a 200–300 word analysis referencing your actual numbers. Requires the same `[provider]` config as `--labels`. Results are cached in `~/.cache/hindsight/summaries.json` keyed by model + report data — re-runs with the same data make no API call. Use `--force-new` to bypass the cache (e.g. after switching models).

**Thinking models** — If your LLM endpoint serves a reasoning/thinking model (qwen3, deepseek-r1, etc.), it must suppress thinking tokens or they exhaust the token budget before writing the answer. llama.cpp supports this via `chat_template_kwargs`:

```toml
# ~/.config/hindsight/config.toml
[provider]
base_url = "http://your-llamacpp-server/v1"
api_key  = "none"
model    = "Qwen3.6-35B-A3B-MXFP4_MOE.gguf"
```

hindsight automatically passes `{"enable_thinking": false}` via `chat_template_kwargs` to llama.cpp. Ollama does not reliably honor this flag via its OpenAI-compatible endpoint — use llama.cpp or a non-thinking model with Ollama.

**Sharing with teammates** — use `hindsight bundle` to create a zip of your session data, then teammates run `full-report --source` against it on their own machine. No server required.

```bash
# On your machine:
hindsight bundle                    # → hindsight-bundle-20260531.zip

# On a teammate's machine:
hindsight full-report --source hindsight-bundle-20260531.zip --output report.md
```

The bundle contains only `.jsonl` session files — no credentials, settings, or other config. It does contain your full prompt history; only share with people you trust. For individual commands, point at the extracted directory via `CLAUDE_CONFIG_DIR=/path/to/extracted hindsight patterns`.

---

## Multi-machine usage

If you use Claude Code across multiple machines, run `bundle` on each one and merge the zips before analysis.

```bash
# On each machine:
hindsight bundle                    # → hindsight-bundle-YYYYMMDD.zip
```

Transfer all zips to one machine, then:

```bash
mkdir merged
for zip in machine1.zip machine2.zip machine3.zip; do
    unzip -o "$zip" -d merged/
done
hindsight full-report --source merged/
```

Works because session files are named by UUID — no collisions when merging. Any `hindsight` command that accepts `--source` works against the merged directory.

---

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
| Coding | `Edit`, `Write`, `apply_patch`, or `write_file` used |
| Feature Dev | add/create/implement keywords + edits |
| Refactoring | refactor/rename/simplify + edits |
| Debugging | error/fix/bug keywords + tool use |
| Testing | pytest/jest/go test in shell |
| Exploration | Read/Grep/Glob/WebSearch/`read_file`/`search_files` only |
| Planning | EnterPlanMode / TaskCreate tools |
| Delegation | Agent / Task tool spawn |
| Git Ops | git push/commit/merge in shell |
| Build/Deploy | docker/npm build/pip install in shell |
| Brainstorming | brainstorm/design keywords, no edits |
| Conversation | No tools, pure text |
| General | Skill tool or uncategorized |

Codex tool names (`exec_command`, `apply_patch`, `write_file`, `read_file`, `search_files`) map into the same categories as their Claude equivalents.

## Data sources

**Claude Code (`--tool claude`, default)**
- `~/.claude/projects/<sanitized-cwd>/<session-id>.jsonl`
- Override base path with `CLAUDE_CONFIG_DIR` env var
- macOS: `~/Library/Application Support/Claude/local-agent-mode-sessions/`

Turns deduplicated by `message.id`. Skill body injections, task notifications, system XML blocks, and terminal output pasted as prompts are stripped from user text before analysis.

**Codex CLI (`--tool codex`)**
- `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`

Token counts are accumulated from per-API-call `last_token_usage` deltas within each task turn (bounded by `task_started` / `task_complete` events). Codex sessions have no `cache_write` equivalent — that column always shows 0. Tool names (`exec_command`, `apply_patch`, etc.) map into the same activity classification used for Claude.

Date filtering is per-entry timestamp for both tools, so sessions spanning midnight are bucketed correctly.

## Development

```bash
git clone https://github.com/scheidydude/hindsight
cd hindsight
uv venv .venv --python 3.11
uv pip install -e .
pytest
hindsight status
```

Optional extras for semantic clustering:

```bash
uv pip install -e ".[semantic]"
hindsight semantic
```

Requires Python 3.11+.
