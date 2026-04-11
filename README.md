# commonplace-plugin

Claude Code plugin for [commonplace](https://github.com/saikatkumardey/commonplace) — long-term memory for AI agents.

Teaches Claude Code when and how to use the `commonplace` CLI to store and recall memories across sessions. Also installs session hooks for automatic recall at startup and summarization at shutdown.

## Prerequisites

Install the commonplace binary first:

```bash
curl -fsSL https://raw.githubusercontent.com/saikatkumardey/commonplace/master/install.sh | sh
```

## Install Plugin

```bash
claude plugin add saikatkumardey/commonplace-plugin
```

Then run the setup skill once to install the hooks:

```
/commonplace setup
```

## What It Does

Once installed and set up, Claude Code will automatically:

- **Recall** relevant memories at the start of every session (SessionStart hook)
- **Store** new facts when it learns preferences, resolves errors, or makes decisions
- **Summarize** the session using Claude Haiku when it ends, writing a 2-4 bullet summary to `session-log` (Stop hook)
- **Extract** structured entries from the session transcript into `preferences`, `decisions`, `errors`, and `context` topics automatically
- **Search** across all memory topics when it needs context from past sessions

## Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `/commonplace` | Memory tasks | Teaches Claude the CLI interface and when to use it |
| `/commonplace setup` | Run once after install | Copies hooks to `~/.claude/hooks/` and wires them into `settings.json` |

## Hooks

The setup skill installs two hooks:

**SessionStart** — `hooks/session-start.py`
Injects recent commonplace entries as additional context at the start of every session. Claude sees your past decisions, preferences, and context before responding to the first message.

**Stop** — `hooks/session-summarize.py`
When the session ends, reads the session transcript and uses `claude -p` (Haiku) to:
1. Generate a 2-4 bullet summary and write it to `session-log`
2. Extract structured entries into `preferences`, `decisions`, `errors`, and `context` topics — only entries genuinely worth remembering, with keyword-rich text for BM25 search

Runs async so it doesn't block exit.

## How Memory Works

```bash
commonplace write <topic> <entry>      # save a memory
commonplace read <topic>               # read a full topic
commonplace search <query>             # BM25 search across all topics
commonplace topics                     # list all topics
commonplace forget <topic> <search>    # remove entries
```

Memories are stored as plain markdown files in `~/.commonplace/` — human-readable and human-editable.

