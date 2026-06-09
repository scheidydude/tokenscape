# token-burn report — 30days (2026-05-03 to 2026-06-01)
*Generated 2026-06-01 02:55 UTC*

## Summary

**209.6M** total tokens · **3,190** turns · **100.0%** cache hit

| Model      | Turns | Tokens | Avg/turn |
| ---------- | ----- | ------ | -------- |
| Sonnet 4.6 | 3,106 | 205.5M | 66.2k    |
| Haiku 4.5  | 84    | 4.1M   | 48.4k    |

## Projects

| Project                        | Turns | Tokens |
| ------------------------------ | ----- | ------ |
| Scheidy's Notes                | 965   | 53.5M  |
| token-burn                     | 485   | 38.9M  |
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
| token-burn                     | high conversation | 59% conversation (287/485 turns) |
| project-03-agentic-mcp         | high conversation | 59% conversation (86/146 turns)  |
| project-02-llm-gateway         | high conversation | 57% conversation (62/109 turns)  |
| orchid                         | high conversation | 57% conversation (220/389 turns) |
| repo-vizualizer                | high conversation | 53% conversation (23/43 turns)   |
| project-01-rag-architecture    | high conversation | 53% conversation (122/230 turns) |
| project-04-observability-evals | high conversation | 43% conversation (63/146 turns)  |

## Model Efficiency

| Model      | Turns | Tokens | Avg/turn | Activities                                                                                                      |
| ---------- | ----- | ------ | -------- | --------------------------------------------------------------------------------------------------------------- |
| Sonnet 4.6 | 3,106 | 205.5M | 66.2k    | Conversation 49%<br>Coding 18%<br>Exploration 17%<br>General 12%<br>Git Ops 2%<br>Testing 2%<br>Build/Deploy 1% |
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
| token-burn                     | Sonnet 4.6 | 485   | 38.9M  | 80.2k    | Conversation 59%<br>Coding 15%<br>General 11%<br>Exploration 5%<br>Testing 5%<br>Git Ops 4%<br>Build/Deploy 1% |
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
The developer exhibits a highly conversational workflow, prioritizing dialogue over direct code generation. With **3,190 total turns**, **Conversation** dominates usage, accounting for **48.9%** of Sonnet 4.6 activity and an overwhelming **86.9%** of Haiku 4.5 usage. This suggests a pattern of iterative refinement and architectural discussion rather than rapid, automated implementation. The top project, **"Scheidy's Notes,"** consumed **965 turns** and **53.5M tokens**, indicating significant context-heavy maintenance or documentation work. Meanwhile, projects like **"prompt-fun"** show extreme conversation density (100%), hinting at experimental or exploratory coding styles where the AI acts as a brainstorming partner. The high session count (**97**) and mean ramp of **13.6 turns** confirm frequent, sustained interactions rather than quick, isolated fixes.

### 2. Token Efficiency
Token efficiency is exceptionally high due to a **100% cache hit rate**, meaning nearly all context was reused from previous turns, drastically reducing redundant processing. However, the average token consumption per turn is substantial: **66,170 tokens** for Sonnet 4.6 and **48,439** for Haiku 4.5. This high volume is driven by the "cheap activity overhead" signal, where **63%** of Sonnet turns and **95%** of Haiku turns were spent on low-value activities like general conversation or Git Ops. While caching mitigates cost, the sheer volume of tokens spent on non-coding tasks represents significant computational waste.

### 3. Model Selection
Model selection shows a clear, logical split. **Sonnet 4.6** handles the heavy lifting (**3,106 turns**), focusing on complex **Coding (17.5%)** and **Exploration (16.8%)** tasks. **Haiku 4.5** is correctly reserved for lightweight, high-frequency interactions (**84 turns**), primarily **Conversation (86.9%)**. This segregation is effective; Haiku’s lower cost and speed are utilized for quick queries, while Sonnet’s reasoning capabilities are applied to substantive development work. The data suggests the user understands the value proposition of each model tier.

### 4. Recommended Actions
1.  **Reduce Sonnet Usage for Conversations:** Since **63%** of Sonnet turns are low-value conversations, switch these specific interactions to Haiku 4.5 to save Sonnet capacity for actual coding tasks.
2.  **Automate Shell Commands:** The frequent use of `git add` (51 times) and `grep -n` (48 times) suggests manual oversight. Implement shell automation or Claude Code’s built-in shell execution to handle these repetitive Git and search operations automatically.
3.  **Optimize Context for "Scheidy's Notes":** Given this project’s massive token usage (**53.5M**), review context window management. Consider splitting large files or using more specific file references to reduce the baseline context size per turn.
4.  **Limit Exploration Turns:** For projects like **"prompt-fun,"** set strict turn limits or use Haiku for initial brainstorming before engaging Sonnet for final implementation, reducing the 100% conversation ratio.
