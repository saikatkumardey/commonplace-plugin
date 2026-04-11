#!/usr/bin/env python3
"""
Stop hook: summarize the just-ended Claude Code session and write structured
entries to commonplace. Runs async after session ends. Installs via /commonplace setup.

Writes:
  - session-log: brief bullet summary (2-4 points)
  - preferences: user style/preference discoveries
  - decisions: architectural or product decisions made
  - errors: bugs resolved with root cause + fix
  - context: new facts about systems, projects, or setup
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECTS_DIR = Path.home() / ".claude/projects"


def get_latest_session():
    """Get the most recently modified session file across all projects."""
    files = sorted(PROJECTS_DIR.rglob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


def extract_conversation(session_file):
    """Extract user/assistant messages from session JSONL."""
    messages = []
    try:
        with open(session_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if entry.get("type") in ("user", "assistant"):
                    msg = entry.get("message") or {}
                    content = msg.get("content", "") if isinstance(msg, dict) else ""
                    if isinstance(content, list):
                        text_parts = [
                            block.get("text", "")
                            for block in content
                            if isinstance(block, dict) and block.get("type") == "text"
                        ]
                        content = " ".join(text_parts)
                    if content and isinstance(content, str):
                        messages.append(f"{entry['type'].upper()}: {content[:600]}")
    except Exception as e:
        print(f"Error reading session: {e}", file=sys.stderr)
    return messages


def run_claude(prompt, timeout=45):
    env = {**os.environ, "CLAUDECODE": ""}
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", "claude-haiku-4-5"],
        capture_output=True, text=True, env=env, timeout=timeout
    )
    return result.stdout.strip() if result.returncode == 0 else None


def summarize(convo):
    """Generate a 2-4 bullet summary of the session."""
    prompt = f"""Summarize this Claude Code session in 2-4 bullet points. Focus on: what was built/fixed/decided. Be terse. No fluff.

Session:
{convo}

Bullet points only, no preamble:"""
    return run_claude(prompt, timeout=30)


def extract_structured(convo, today):
    """
    Extract memory-worthy facts from the session, categorized by topic.
    Returns a dict: {topic -> [entry, ...]}
    """
    prompt = f"""You are reviewing a Claude Code session transcript. Extract structured memory entries for long-term storage.

For each category below, output ONLY entries that are genuinely worth remembering — skip empty categories entirely.

Categories:
- preferences: user preferences, style choices, things they explicitly like/dislike
- decisions: architectural or product decisions made
- errors: errors or bugs resolved (include root cause + fix)
- context: new facts about the user's systems, projects, or setup worth knowing later

Output format — one JSON object, keys are category names, values are arrays of strings (one entry per item). Each entry should be 1-2 sentences, keyword-rich, standalone (no pronouns, include relevant nouns). If a category has nothing worth writing, omit it.

Example:
{{"preferences": ["User prefers plain text output, no markdown bold/italic in responses"], "errors": ["hugo-book theme: tables break with wide content — switched to grouped list layout as workaround"]}}

Session (last 50 turns):
{convo}

JSON only, no preamble:"""

    raw = run_claude(prompt, timeout=45)
    if not raw:
        return {}
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except Exception:
        return {}


def cp_write(topic, entry):
    subprocess.run(
        ["commonplace", "write", topic, entry],
        capture_output=True, timeout=10
    )


def main():
    session_file = get_latest_session()
    if not session_file:
        return

    messages = extract_conversation(session_file)
    if len(messages) < 3:
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    convo = "\n".join(messages[-50:])

    # 1. Session log summary
    summary = summarize(convo)
    if summary:
        cp_write("session-log", f"[{today}] Session summary:\n{summary}")

    # 2. Structured extractions into proper topics
    structured = extract_structured(convo, today)
    valid_topics = {"preferences", "decisions", "errors", "context"}
    for topic, entries in structured.items():
        if topic not in valid_topics:
            continue
        for entry in entries:
            if entry and len(entry) > 10:
                cp_write(topic, f"[{today}] {entry}")


if __name__ == "__main__":
    main()
