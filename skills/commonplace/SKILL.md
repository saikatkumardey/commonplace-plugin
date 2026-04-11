---
name: commonplace
description: "Long-term memory via commonplace CLI. Use when you learn something worth remembering (preferences, decisions, errors, context), at the start of tasks to recall past context, or when the user asks you to remember or recall something."
---

# Commonplace Memory

You have access to `commonplace`, a persistent long-term memory tool. Use it to remember facts, decisions, preferences, and context across sessions.

## Commands

```bash
commonplace write <topic> <entry>        # Save a memory (warns if duplicate)
commonplace write <topic> <entry> --force # Skip duplicate check
commonplace read <topic>                  # Read all entries in a topic
commonplace search <query> [--limit N]    # Hybrid BM25 + semantic search
commonplace search <query> --semantic     # Force semantic-only path
commonplace topics                        # List all topics
commonplace forget <topic> <search>       # Remove matching entries
commonplace init                          # Download embedding model (one-time)
commonplace embed                         # Backfill entries into semantic index
```

## When to Store

Store immediately when any of these happen:

- **Error resolved** → `commonplace write errors "description of error and fix"`
- **Decision made** → `commonplace write decisions "what was chosen and why"`
- **User preference discovered** → `commonplace write preferences "what they prefer"`
- **Significant task completed** → `commonplace write context "what was done"`

## When to Recall

At the start of a task, search for relevant past context:

```bash
commonplace search "relevant keywords"
```

Also recall when the user references something from a previous session, or when you need context you don't have.

## Writing Good Entries

Search is hybrid BM25 + semantic. Include synonyms and related terms so entries are findable:

```bash
# Bad — may not match "test driven development"
commonplace write preferences "likes TDD"

# Good — matches both keyword and semantic search
commonplace write preferences "likes TDD (test-driven development), always write tests first"
```

## Suggested Topics

| Topic | What goes in it |
|-------|----------------|
| `preferences` | How the user likes to work, coding style, communication preferences |
| `decisions` | Technical choices and their rationale |
| `errors` | Bugs encountered and how they were fixed |
| `context` | Project descriptions, architecture, infrastructure notes |
| `people` | Who the user is, their skills, their role |

Topics are auto-created on first write. Use whatever topic names make sense — these are suggestions, not a fixed list.

## What Not to Store

- Ephemeral task state (use your conversation context for that)
- Exact file contents or code (read the files instead)
- Anything already in CLAUDE.md or project docs
