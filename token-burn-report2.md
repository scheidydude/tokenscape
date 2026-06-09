# token-burn report — 30days (2026-05-03 to 2026-06-01)
*Generated 2026-06-01 02:59 UTC*

## Summary

**209.7M** total tokens · **3,191** turns · **100.0%** cache hit

| Model      | Turns | Tokens | Avg/turn |
| ---------- | ----- | ------ | -------- |
| Sonnet 4.6 | 3,107 | 205.6M | 66.2k    |
| Haiku 4.5  | 84    | 4.1M   | 48.4k    |

## Projects

| Project                        | Turns | Tokens |
| ------------------------------ | ----- | ------ |
| Scheidy's Notes                | 965   | 53.5M  |
| token-burn                     | 486   | 39.0M  |
| orchid                         | 389   | 23.4M  |
| project-01-rag-architecture    | 230   | 20.1M  |
| codeindex                      | 265   | 16.4M  |
| project-05-security-compliance | 127   | 12.9M  |
| project-03-agentic-mcp         | 146   | 10.5M  |
| project-04-observability-evals | 146   | 9.8M   |

## Workflow

| From         | To           | Count | %   |
| ------------ | ------------ | ----- | --- |
| Conversation | Coding       | 216   | 14% |
| Coding       | Conversation | 206   | 38% |
| Conversation | General      | 202   | 13% |
| General      | Conversation | 197   | 50% |
| Conversation | Exploration  | 124   | 8%  |
| Exploration  | Conversation | 113   | 22% |
| Git Ops      | Conversation | 54    | 93% |
| Exploration  | Coding       | 37    | 7%  |

**Session ramp** — mean 13.6 turns to first edit · p90 23 · 97 sessions

## Growth Signals

| Project                        | Signal            | Detail                           |
| ------------------------------ | ----------------- | -------------------------------- |
| prompt-fun                     | high conversation | 100% conversation (8/8 turns)    |
| outputs                        | high conversation | 88% conversation (7/8 turns)     |
| .claude                        | high conversation | 82% conversation (18/22 turns)   |
| jumblekit                      | high conversation | 80% conversation (4/5 turns)     |
| series-brain                   | high conversation | 73% conversation (85/116 turns)  |
| portal                         | high conversation | 73% conversation (8/11 turns)    |
| ai-path-learning               | high conversation | 70% conversation (21/30 turns)   |
| markdown-viewer                | high conversation | 68% conversation (13/19 turns)   |
| utilities                      | high conversation | 68% conversation (15/22 turns)   |
| ai-platform-architecture       | high conversation | 67% conversation (16/24 turns)   |
| codeindex                      | high conversation | 63% conversation (166/265 turns) |
| scheidydudes-github-repos      | high conversation | 62% conversation (5/8 turns)     |
| token-burn                     | high conversation | 59% conversation (288/486 turns) |
| project-03-agentic-mcp         | high conversation | 59% conversation (86/146 turns)  |
| project-02-llm-gateway         | high conversation | 57% conversation (62/109 turns)  |
| orchid                         | high conversation | 57% conversation (220/389 turns) |
| repo-vizualizer                | high conversation | 53% conversation (23/43 turns)   |
| project-01-rag-architecture    | high conversation | 53% conversation (122/230 turns) |
| project-04-observability-evals | high conversation | 43% conversation (63/146 turns)  |

## Model Efficiency

| Model      | Turns | Tokens | Avg/turn | Activities                                                                                                      |
| ---------- | ----- | ------ | -------- | --------------------------------------------------------------------------------------------------------------- |
| Sonnet 4.6 | 3,107 | 205.6M | 66.2k    | Conversation 49%<br>Coding 18%<br>Exploration 17%<br>General 12%<br>Git Ops 2%<br>Testing 2%<br>Build/Deploy 1% |
| Haiku 4.5  | 84    | 4.1M   | 48.4k    | Conversation 87%<br>General 8%<br>Exploration 5%                                                                |

| Model      | Signal                  | Detail                                                                |
| ---------- | ----------------------- | --------------------------------------------------------------------- |
| Sonnet 4.6 | cheap activity overhead | 63% of turns in low-value activities (Conversation, General, Git Ops) |
| Haiku 4.5  | cheap activity overhead | 95% of turns in low-value activities (Conversation, General)          |

**By project**

| Project                        | Model      | Turns | Tokens | Avg/turn | Activities                                                                                                     |
| ------------------------------ | ---------- | ----- | ------ | -------- | -------------------------------------------------------------------------------------------------------------- |
| .claude                        | Sonnet 4.6 | 22    | 549.0k | 25.0k    | Conversation 82%<br>General 14%<br>Exploration 5%                                                              |
| Scheidy's Notes                | Sonnet 4.6 | 965   | 53.5M  | 55.5k    | Exploration 45%<br>Conversation 32%<br>Coding 15%<br>General 7%<br>Build/Deploy 0%                             |
| ai-path-learning               | Sonnet 4.6 | 30    | 957.2k | 31.9k    | Conversation 70%<br>General 17%<br>Coding 7%<br>Git Ops 3%<br>Exploration 3%                                   |
| ai-platform-architecture       | Sonnet 4.6 | 24    | 1.4M   | 58.1k    | Conversation 67%<br>Coding 29%<br>General 4%                                                                   |
| codeindex                      | Sonnet 4.6 | 253   | 15.8M  | 62.5k    | Conversation 61%<br>General 21%<br>Coding 7%<br>Git Ops 5%<br>Exploration 4%<br>Testing 1%<br>Build/Deploy 0%  |
|                                | Haiku 4.5  | 12    | 539.2k | 44.9k    | Conversation 92%<br>General 8%                                                                                 |
| jumblekit                      | Sonnet 4.6 | 5     | 92.7k  | 18.5k    | Conversation 80%<br>Git Ops 20%                                                                                |
| markdown-viewer                | Sonnet 4.6 | 19    | 891.4k | 46.9k    | Conversation 68%<br>Coding 21%<br>Exploration 5%<br>General 5%                                                 |
| notes                          | Sonnet 4.6 | 12    | 271.5k | 22.6k    | General 58%<br>Conversation 33%<br>Exploration 8%                                                              |
| orchid                         | Sonnet 4.6 | 335   | 20.9M  | 62.4k    | Conversation 53%<br>General 27%<br>Coding 10%<br>Testing 4%<br>Exploration 4%<br>Git Ops 2%<br>Build/Deploy 1% |
|                                | Haiku 4.5  | 54    | 2.5M   | 46.8k    | Conversation 81%<br>General 11%<br>Exploration 7%                                                              |
| outputs                        | Sonnet 4.6 | 8     | 229.5k | 28.7k    | Conversation 88%<br>General 12%                                                                                |
| portal                         | Sonnet 4.6 | 11    | 943.2k | 85.7k    | Conversation 73%<br>Coding 18%<br>Build/Deploy 9%                                                              |
| project-01-rag-architecture    | Sonnet 4.6 | 230   | 20.1M  | 87.5k    | Conversation 53%<br>Coding 27%<br>General 13%<br>Exploration 3%<br>Build/Deploy 2%<br>Git Ops 1%<br>Testing 0% |
| project-02-llm-gateway         | Sonnet 4.6 | 109   | 9.3M   | 84.9k    | Conversation 57%<br>Coding 23%<br>General 10%<br>Git Ops 5%<br>Build/Deploy 4%<br>Exploration 2%               |
| project-03-agentic-mcp         | Sonnet 4.6 | 146   | 10.5M  | 71.6k    | Conversation 59%<br>Coding 23%<br>General 8%<br>Exploration 6%<br>Build/Deploy 3%<br>Git Ops 1%                |
| project-04-observability-evals | Sonnet 4.6 | 146   | 9.8M   | 67.4k    | Coding 46%<br>Conversation 43%<br>General 6%<br>Git Ops 3%<br>Exploration 2%                                   |
| project-05-security-compliance | Sonnet 4.6 | 127   | 12.9M  | 101.5k   | Coding 41%<br>Conversation 38%<br>General 10%<br>Testing 9%<br>Exploration 1%<br>Git Ops 1%                    |
| prompt-fun                     | Sonnet 4.6 | 8     | 358.9k | 44.9k    | Conversation 100%                                                                                              |
| repo-vizualizer                | Sonnet 4.6 | 43    | 2.4M   | 54.7k    | Conversation 53%<br>General 26%<br>Coding 12%<br>Exploration 9%                                                |
| scheidydudes-github-repos      | Sonnet 4.6 | 8     | 176.1k | 22.0k    | Conversation 62%<br>General 38%                                                                                |
| series-brain                   | Sonnet 4.6 | 98    | 4.9M   | 49.6k    | Conversation 68%<br>Exploration 12%<br>Coding 10%<br>General 6%<br>Git Ops 2%<br>Build/Deploy 1%               |
|                                | Haiku 4.5  | 18    | 1.0M   | 55.8k    | Conversation 100%                                                                                              |
| token-burn                     | Sonnet 4.6 | 486   | 39.0M  | 80.2k    | Conversation 59%<br>Coding 15%<br>General 11%<br>Exploration 5%<br>Testing 5%<br>Git Ops 4%<br>Build/Deploy 1% |
| utilities                      | Sonnet 4.6 | 22    | 733.9k | 33.4k    | Conversation 68%<br>Exploration 14%<br>Coding 14%<br>General 5%                                                |

## Patterns

**Top shell commands**

| Command                                                  | Runs | Projects           |
| -------------------------------------------------------- | ---- | ------------------ |
| git add                                                  | 51   | codeindex, orchid  |
| grep -n                                                  | 48   | codeindex, orchid  |
| python3 -c                                               | 33   | codeindex, orchid  |
| uv run                                                   | 25   | orchid, token-burn |
| find "/Users/david/Library/CloudStorage/Dropbox/Obsidian | 23   | Scheidy's Notes    |

**Hottest files**

| File                                                                                                             | Edits |
| ---------------------------------------------------------------------------------------------------------------- | ----- |
| /Users/david/Development/scheidydudes-github-repos/ai-path-learning/project-04-observability-evals/docs/index.md | 17    |
| /Users/david/Development/scheidydudes-github-repos/ai-path-learning/project-04-observability-evals/task_plan.md  | 15    |
| /Users/david/Development/scheidydudes-github-repos/ai-path-learning/project-01-rag-architecture/INDEX.md         | 14    |
| /Users/david/Development/scheidydudes-github-repos/ai-path-learning/project-05-security-compliance/INDEX.md      | 12    |
| /Users/david/Development/scheidydudes-github-repos/token-burn/src/token_burn/cli.py                              | 12    |

**Prompt verbs**

| Verb    | Count |
| ------- | ----- |
| add     | 7     |
| update  | 5     |
| start   | 5     |
| changes | 4     |
| phase   | 3     |
| mcp     | 3     |
| using   | 3     |
| check   | 3     |
| push    | 3     |
| create  | 3     |

**Prompt bigrams**

| Bigram        | Count |
| ------------- | ----- |
| mcp server    | 9     |
| token burn    | 6     |
| weeks ago     | 6     |
| codeindex mcp | 5     |
| update readme | 4     |
| start phase   | 4     |
| cli commands  | 3     |
| add option    | 3     |
| brief line    | 3     |
| line purpose  | 3     |

## Intent Clusters

*104 prompts · k=7 · BAAI/bge-small-en-v1.5*

**Cluster 1** (33 prompts, 32%)
- *bump to 0.2.0 and tag it.*
- *update the README with the new CLI commands*

**Cluster 2** (19 prompts, 18%)
- *add that line to CLAUDE.md in the ../orchid folder*
- *refactor this repo back to the name "token-burn".  Note in the README.md that it is only Claude righ…*

**Cluster 3** (16 prompts, 15%)
- *yes, start Phase 2, do a commit between phases*
- *start phase 2*

**Cluster 4** (16 prompts, 15%)
- *check the local .claude settings json  for the codeindex MCP server*
- *check the .claude/settings.json - why is the codeindex mcp server not properly working for claude wh…*

**Cluster 5** (7 prompts, 7%)
- *increase the timeout, when running a report print a status indicator in the console*
- *make no changes.  Can we add a --full-run-report function that generates a md report for full review…*

**Cluster 6** (7 prompts, 7%)
- *documane Orchid vs Agentic OS and what's missing that would make it a real agentic OS in a md file a…*
- *Audit the Orchid repo at /Users/david/Development/scheidydudes-github-repos/orchid for an Agentic OS…*

**Cluster 7** (6 prompts, 6%)
- *all 5 phases are complete, correct?*
- *do phase 5*

## AI Insights

# Claude Code Usage Analysis (May 3 – June 1, 2026)

### 1. Usage Patterns
The developer exhibits a heavy conversational workflow rather than a purely code-generation focus. Across 3,191 turns, **Sonnet 4.6** dominates with 3,107 turns, yet nearly half (49%) are categorized as "Conversation." This is reinforced by the `growth_signals` data, where projects like `prompt-fun` (100% conversation) and `outputs` (88% conversation) indicate significant time spent on dialogue rather than implementation. The top projects, `Scheidy's Notes` (965 turns) and `token-burn` (486 turns), suggest a mix of knowledge management and experimental coding. The `session_ramp_mean` of 13.6 turns implies moderate session depth, while the `prompt_verbs` list (dominated by "add," "update," and "start") reflects an iterative, incremental development style.

### 2. Token Efficiency
Token efficiency is surprisingly high due to a **100% cache hit rate**, meaning the model is effectively reusing context rather than reprocessing it. However, there is significant waste in activity allocation. Sonnet 4.6 averages 66,168 tokens per turn, but **63% of its turns** are in "low-value" activities like Conversation, General chat, and Git Ops. Similarly, Haiku 4.5 sees 95% of its turns in these low-value categories. This suggests that expensive reasoning capabilities are being underutilized for complex tasks, while the model is largely acting as a conversational partner or simple command executor.

### 3. Model Selection
Model selection appears misaligned with task complexity. **Haiku 4.5** is used for only 84 turns (2.6% of total), yet 95% of those are low-value conversations. This indicates Haiku is not being leveraged for its intended purpose: fast, cheap execution of simple tasks. Conversely, **Sonnet 4.6** handles 97.4% of the workload, including a massive portion of conversational turns that likely do not require its advanced reasoning capabilities. The data shows a "heavy hammer" approach, where the most capable and expensive model is used for tasks that could be handled by lighter models or automated scripts.

### 4. Recommended Actions
1.  **Shift Conversational Turns to Haiku:** Immediately route "Conversation" and "General" activities to Haiku 4.5. Given that 63% of Sonnet’s turns are low-value, this would drastically reduce token consumption and cost without sacrificing quality for simple queries.
2.  **Automate Shell Repetitions:** The `shell_automation_candidates` show frequent use of `git add` (51 times) and `grep -n` (48 times). Implement custom Claude Code commands or aliases for these common operations to reduce manual turn overhead.
3.  **Refine Project Context:** For projects like `prompt-fun` and `outputs` with >80% conversation rates, evaluate if these are truly development projects or just brainstorming spaces. Consider archiving non-code interactions to keep the primary workspace focused on high-value coding activities.
4.  **Audit "Exploration" Usage:** With 16.8% of Sonnet’s usage dedicated to "Exploration," ensure this is not redundant with the "Conversation" category. If exploration is merely asking questions, move it to Haiku to free up Sonnet for actual coding tasks.
